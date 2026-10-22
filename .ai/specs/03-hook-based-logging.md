# Spec 03 — Correlated Run-Log Step Recording Through Harness Hooks

**Status:** Proposed; design and acceptance contract only (not implemented).  
**Date:** 2026-10-22.  
**Canonical path:** `.ai/specs/03-hook-based-logging.md`.  
**Source:** Original spec 03 and its 2026-10-21 review integration; detailed SDD design dated 2026-10-22.  
**Decisions:** ADR-0009, Decisions 2 and 5; ADR-0011.  
**Dependencies:** Completed spec 02 (run-log vocabulary/validation); spec 13 (`harness/` abstraction, capabilities, and project registry) must land before hook deployment.  
**Downstream consumer:** Spec 05 (usage, cost, and aggregated duration telemetry).  
**Intended change surface:** Canonical rule, hook adapter, dispatch envelope, producer, installer, orchestrator workflows, retrospective, and offline tests.

## 1. Source and problem statement

Run `4305eda1` recorded all twelve `step` entries retroactively at run end, each with `duration_s: 0`. The current run-log rule instructs the model to call `scripts/log-step.sh step` after each workflow step, but nothing enforces that call when the boundary occurs. Today the producer calculates `duration_s` from the preceding **accepted log event** (`last_epoch`), not from the actual start of the skill. Deferred calls, concurrent agents, and nesting therefore distort measurement.

Spec 02 is already complete. Its case-sensitive vocabularies, precise legacy normalization, validation-before-mutation, exit-zero telemetry failures, read-only `lint`, and retrospective exclusions are binding invariants. The current checkout does not yet contain `harness/`; spec 13 owns its introduction, capability table, and registered-project list. Spec 03 must build on that architecture rather than creating an incompatible, provider-specific deployment path.

Claude Code's `Stop` means a main-agent response stopped; `SubagentStop` means a subagent response stopped. Neither is a universal "workflow skill finished" event. One turn may invoke multiple skills; a subagent may produce multiple checkpoint reports. Declaring `hooks: yes` means the harness has a hook mechanism, **not** that every workflow-step boundary is observable.

**Attribution hazard:** Two runs may be active in the same registered project, possibly in the same session. Current working directory, most-recent timestamps, an agent type, or "only one active run" are not sufficient evidence that a stop belongs to a specific run. Missing evidence must lower coverage, never attach an event to another run.

## 2. Goal and measurable result

Move recording of **reliably observed** step boundaries from model-authored instructions to deterministic, user-level Claude Code hooks invoking the existing `scripts/log-step.sh step` producer. Every automatically accepted step must be associated with an explicit, verifiable chain:

`run_id → session_id → agent_id|main → dispatch_id → checkpoint_id → invoked skill`

and a trustworthy start/end interval.

Success means an accepted hook event refers to exactly one checkpoint; replay cannot append another accepted event; and unobserved steps remain visibly approximate or uncovered. A missing measurement must never be represented as zero. Keep `run-start` and `run-end` prompt-driven in the orchestrator.

## 3. Scope

**In scope:** `SubagentStop` and `Stop`; optional auxiliary events strictly needed to bind identities or establish start times; explicit dispatch envelopes; checkpoint state and idempotency; safe user-level hook installation/uninstallation; registered-project guard; compatible producer, lint, and `/retro` changes; timing denominators; offline fixture tests; selective workflow-prompt removal.

**Out of scope:** Token and cost accounting (spec 05); git rails (spec 06); migration or rewriting historical logs; installing hooks in consumer-repository `.claude/settings.json`; model-powered/paid experiments; granting subagents write ownership of shared `.ai/`; treating an agent's claim as independent quality validation.

## 4. Binding design decisions

**D-01 — Separate evidence for identity and step name.** The orchestrator/dispatcher supplies `run_id`, `session_id`, `dispatch_id`, `checkpoint_id`, target agent, and expected skill in a structured dispatch envelope. The actual step name comes only from a verified structured invocation of the installed skill (for example, a validated `Skill` tool call in a scoped transcript), never from the agent's narrative report. The expected skill alone is not invocation evidence.

**D-02 — Reported outcome is not a quality verdict.** `outcome` comes only from one exact, machine-readable checkpoint report marker matching the envelope. It remains an **agent-reported** result. Normal prose, `DONE`, `NEEDS WORK`, and inferred sentiment cannot supply a definitive outcome, and `gate`/`tests` cannot be manufactured by the adapter.

**D-03 — Fail closed on attribution.** Never choose the newest run, nearest timestamp, a single active run, the working directory alone, or a likely agent. `step: unknown` is permitted only after run and checkpoint correlation is unambiguous and all other fields required for that record are reliable; it is not a way to resolve conflicting candidate skills.

**D-04 — Select recording per boundary.** `hooks: yes` authorizes an attempt, not prompt removal. To claim an observed step requires an envelope, verified agent/checkpoint association, a reliable boundary, a valid outcome marker, and sufficient timing evidence. All other boundaries retain prompt-driven `note: approximate` recording or are marked explicitly uncovered.

**D-05 — Preserve spec 02.** The eight-lowercase-hex run ID, existing CLI commands, vocabularies, alias normalization, linter behavior for legacy rows, and append-only history remain valid. New controlled fields are validated together before mutation.

**D-06 — Instrumentation must not interrupt work.** Hooks perform bounded local processing, return process exit code `0` on every failure, emit no blocking decision, do not edit transcripts, do not inspect unrelated projects, and do not expose private prompt, source, or credential data in diagnostics.

## 5. Actors and ownership

| Actor | Responsibility | Prohibited behavior |
|---|---|---|
| Orchestrator | Invoke `run-start`, retain its returned ID, register expected checkpoints before dispatch, call `run-end` | Guess outcomes; duplicate a checkpoint already accepted by a hook |
| Dispatcher | Persist and hand off a structured envelope; bind a checkpoint to its real target agent | Resolve identity by scanning active run timestamps |
| Agent | Execute the skill and emit the exact checkpoint report marker | Write the hook-owned `step` record itself |
| Hook adapter | Verify project scope, payload, envelope, invoked skill, report marker, and times; request a producer write | Read history to infer a run; choose the most plausible active run |
| `log-step.sh` producer | Validate, serialize same-run mutations, enforce once-per-checkpoint acceptance, persist compatible JSONL | Partially accept invalid input or fail an observed tool call |
| `/retro` | Read history, lint the selected corpus, classify coverage, compute disjoint time metrics | Invent missing timestamps or sum overlapping worker spans as wall time |

Orchestrator ownership of shared `.ai/` remains unchanged. Correlation files are local operational telemetry, not task-state files.

## 6. Terminology and evidence levels

- **Run:** A successfully persisted `run-start` with its existing run ID. Resuming in another session opens a new run under the current rule.
- **Session:** A harness main-session identity; it is not, by itself, a run identity.
- **Agent:** The main session (`main`) or a subagent with a harness-issued `agent_id`.
- **Dispatch:** An explicit assignment of work, carrying an opaque `dispatch_id`.
- **Checkpoint:** Exactly one expected report boundary, identified by `checkpoint_id`. A resumed agent gets a new checkpoint for its next report.
- **Skill:** A verified structured invocation of an installed workflow skill. An `agent_type` label does not identify the invoked skill.
- **Observed interval:** Elapsed time from a recorded dispatch/skill-start boundary to a matching stop. It can contain scheduling, tool wait, and overhead; it is **not** necessarily active model-compute time.
- **Observed:** Reliable run/checkpoint, start and end, unique invoked skill, and valid reported outcome.
- **Partial:** Some dimensions/boundaries are measured and others are not.
- **Approximate:** Orchestrator-driven legacy timing or a boundary estimated from multiple invocations.
- **Unavailable:** Attribution, outcome, or timing cannot be established; omit an automatic step event instead of fabricating a measurement.
- **Uncovered:** An expected checkpoint has no accepted reliable step observation.

## 7. Normative requirements

| ID | Requirement |
|---|---|
| **REQ-01** | The system **SHALL** correlate every automatically accepted step through explicit `run_id`, `session_id`, `agent_id` or `main`, `dispatch_id`, and `checkpoint_id`, never through project identity, active-run order, or timestamps alone. |
| **REQ-02** | The adapter **SHALL** obtain `step` from a verified structured invoked-skill identifier; free-form model text **SHALL NOT** supply the name. The producer **SHALL** persist `dispatch_id` and `delivery_id` as distinct fields on measured records, retaining the explicit run-to-dispatch chain after active state cleanup. |
| **REQ-03** | The adapter **SHALL** accept `outcome` only from an unambiguous machine-readable marker bound to the checkpoint and valid under spec 02. Absence of a marker **SHALL NOT** default to `ok`. |
| **REQ-04** | The system **SHALL** capture both monotonic endpoints and a verified common clock domain, as well as wall-clock timestamps, for a measured interval. Without comparable monotonic endpoints or a trustworthy start, measured duration **SHALL** be unavailable; `last_epoch` is not a substitute for skill start. Wall-clock jumps **SHALL NOT** inflate monotonic elapsed time. |
| **REQ-05** | Duplicate `Stop`/`SubagentStop` deliveries, repeated markers, or competing hook/prompt paths **SHALL NOT** create more than one accepted step for one checkpoint. `delivery_id` identifies a hook delivery (or a deterministic correlated fingerprint), never the dispatch; checkpoint identity, not delivery identity, enforces step deduplication. |
| **REQ-06** | Ambiguous or absent correlation **SHALL NOT** mutate either of two concurrent runs or their metadata; the adapter **SHALL** emit safe attribution/coverage diagnostics. |
| **REQ-07** | Active envelopes, checkpoint indices, receipts, and coverage state **SHALL** live outside the shared historical `runs/*.jsonl` store. The adapter **SHALL NOT** search that store to attribute an event. Accepted historical measured records **SHALL** retain `dispatch_id`, `delivery_id`, and their identity provenance after active state is removed. |
| **REQ-08** | All spec 02 validation and no-mutation-on-invalid-input invariants **SHALL** hold before log, sequence, accepted receipt, or active metadata changes. |
| **REQ-09** | Producer additions **SHALL** be backward compatible; legacy valid records **SHALL** remain valid under `lint`, with no new outcome values and no changes to specified legacy alias behavior. |
| **REQ-10** | `sync.sh` **SHALL** merge only manifest-owned hook entries into user-level `~/.claude/settings.json`, preserving unrelated settings and supporting idempotent install/uninstall. |
| **REQ-11** | Before reading the JSON payload or correlation data, the hook **SHALL** confirm that its physical current directory is within a project registered in `~/.config/orchestrail/projects` **or** a securely verified Git linked worktree of such a project; otherwise it **SHALL** exit `0` immediately and silently. A worktree **SHALL** require trusted registered-repository membership, canonical path checks, and explicit dispatch authorization, never just `CLAUDE_PROJECT_DIR` or a matching worktree name. |
| **REQ-12** | Recording selection **SHALL** depend on declared capability and actual per-boundary evidence. With `hooks: no`, prompt-driven recording continues and every new step includes literal `note: approximate`. `hooks: yes` alone **SHALL NOT** justify removing an unobserved step instruction. |
| **REQ-13** | For single-session `/phase-*` runs, the adapter **MAY** recognize scoped structured skill calls on a best-effort basis. Multiple skills before one `Stop` **SHALL NOT** be treated as multiple proven completed boundaries. |
| **REQ-14** | Before `run-end`, the orchestrator **SHALL** finalize the inventory of expected checkpoints. Missing inventory **SHALL** mean coverage unknown, never 100%. |
| **REQ-15** | Sequential timing reports **SHALL** disclose nonoverlapping intervals, uncovered gaps, coverage, and the run-wall denominator. Nested/parallel reports **SHALL** distinguish inclusive, observed exclusive, covered union, worker sum, and overlap. Elapsed step time **SHALL** use same-domain monotonic endpoints, with wall-clock discontinuities labeled independently; run wall time **SHALL** disclose its own clock reliability. |
| **REQ-16** | Out-of-order events **SHALL NOT** create negative duration, backdate a start, or append a late step after an accepted `run-end`. |
| **REQ-17** | Acceptance tests **SHALL** execute offline without model calls, real user registry/settings, or real historical run logs. |
| **REQ-18** | `/retro` **SHALL** distinguish measured, approximate, unavailable, and lint-invalid observations, and disclose numerators, denominators, and exclusions. |
| **REQ-19** | Every hook error (payload, filesystem, dependency, parse, timing) **SHALL** exit `0`, avoid a blocking hook response, and omit secrets or source content from diagnostics. |
| **REQ-20** | Hook event names, payload fields, and agent/dispatch binding **SHALL** be verified on the installed target Claude Code version before declaring an adapter boundary reliable; unsupported events **SHALL** fall back to approximate/unavailable coverage. |

## 8. Dispatch envelope and correlation contract

### 8.1. Registration and binding

Following a successful prompt-driven `run-start`, and **before** work is dispatched, register a checkpoint with exact `run_id`, `session_id`, `checkpoint_id`, `dispatch_id`, registered project root, **authorized execution worktree root**, expected skill, and target scope. The envelope's `project_realpath` identifies the registered main checkout; `worktree_realpath` identifies the authorized physical checkout and equals `project_realpath` when no linked worktree is used. `dispatch_id` must be an unpredictable opaque ID, **not** a timestamp. One main session may host multiple runs; the session alone can never select one without a checkpoint.

Proposed commands (subcommand names become normative once implemented):

```bash
scripts/log-step-dispatch.sh prepare \
  --run 4305eda1 --session sess-A --checkpoint cp-red-001 \
  --dispatch d-6b3f9c52 --scope subagent \
  --skill atomic-execution-tests --project "$PROJECT_ROOT" \
  --worktree "$AUTHORIZED_WORKTREE_ROOT"

scripts/log-step-dispatch.sh bind \
  --dispatch d-6b3f9c52 --agent agent-17

scripts/log-step-dispatch.sh coverage \
  --run 4305eda1 --session sess-A
```

At runtime, harness identities must come from **reliable structured sources**. Whether `SessionStart` plus an inherited environment can securely supply `session_id` must be established by fixture and installation checks; neither process names nor chat text qualify. A subagent `agent_id` may become known only after dispatch; prior to a verified association the envelope remains `pending_bind`.

**Platform constraint:** `SubagentStart` can carry `agent_id` without necessarily carrying the dispatch identifier. Bind only through a real common structured identity (for example, an explicit `bind` using a dispatch result, or a validated ticket in a machine-readable invocation field). Binding to the "only recently started" agent, closest timestamp, or matching `agent_type` is prohibited, **even if there is only one candidate**. If no such common identity exists, omit the automated step and record missing coverage. Arbitrary parallel-run support cannot be claimed without a demonstrated association mechanism.

### 8.2. Local active-state layout

Store correlation data in owner-only directories (`0700`), for example:

```text
~/.config/orchestrail/runtime/
  sessions/<session-id>/
    dispatches/<dispatch-id>.json
    agents/<agent-id>.json
  runs/<run-id>/
    checkpoints/<checkpoint-id>.json
    receipts/<checkpoint-id>.json
    coverage.json
```

Records must include `schema_version: 1`, all correlation IDs, canonical registered project root, an explicitly authorized `worktree_realpath`, `expected_skill`, optional `parent_checkpoint_id`, `start_wall_ms`, required `start_mono_ns` and verified `clock_domain` for measured steps, status, provenance for identities/timestamps, and evidence of an observable boundary. The correlated stop supplies `end_wall_ms`, `end_mono_ns` in the same clock domain, and a separate delivery identity; none can be inferred from a dispatch ID. Do not persist prompts, source code, tool outputs, full agent messages, credentials, or arbitrary transcript extracts. Validate ownership, identifiers, file permissions and canonical paths; reject symlinks escaping the state root. Read a transcript only from a harness-supplied path for the **already correlated** session/agent and only to the necessary bounded extent.

This active directory is not a second historical store. After closure and a defined late-event retention window, it may be removed **after** coverage is persisted in the historical `run-end` record (or a separately specified safe historical summary). After a crash, absent receipts mean unknown coverage, not a complete run.

### 8.3. Example versioned envelope

```json
{
  "schema_version": 1,
  "run_id": "4305eda1",
  "session_id": "sess-A",
  "dispatch_id": "d-6b3f9c52",
  "checkpoint_id": "cp-red-001",
  "parent_checkpoint_id": null,
  "scope": "subagent",
  "agent_id": "agent-17",
  "project_realpath": "/synthetic/registered/project",
  "worktree_realpath": "/synthetic/registered/project-linked-worktree",
  "expected_skill": "atomic-execution-tests",
  "skill_evidence": "structured-tool-call",
  "start_wall_ms": 1792656000000,
  "start_mono_ns": 101000000000,
  "clock_domain": "host-boot-A",
  "status": "bound"
}
```

`expected_skill` alone **cannot authorize** a `step` line: match it against independently observed structured invocation evidence. The path is synthetic and must not be replaced in committed fixtures by a user's real path.

### 8.4. Identity and replay keys

Logical accepted-step key: `(run_id, session_id, checkpoint_id)`. Persist `dispatch_id` separately to preserve its causal assignment, and persist `delivery_id` separately to identify the accepted hook delivery. For diagnostics, track a delivered harness event as `(hook_event_name, agent_id|main, delivery_id)`; `delivery_id` is either a genuine harness delivery identifier or a deterministic correlated fingerprint. If the harness lacks a delivery ID, construct the fingerprint from verified structured identities, the event type, and authenticated checkpoint report identity, never arbitrary narrative text or the dispatch ID by itself. Store `delivery_id_source: harness|derived`, use a cryptographic digest for a potentially sensitive raw delivery token (with sufficient collision resistance and documented canonical inputs), and reject conflicting reassignment of either `dispatch_id` or `checkpoint_id`. The full causal chain must be recoverable from accepted JSONL fields after ephemeral dispatch state is deleted.

Each checkpoint can yield at most one accepted step across `hook` and `prompt` paths. A main-agent `Stop` must not close a subagent checkpoint. The first durably accepted outcome is final for that checkpoint; a conflicting later delivery emits a safe warning but does not replace it. Retries and continued agent work require a **new** checkpoint.

## 9. Evidence for invoked skill and reported outcome

### 9.1. Invoked-skill extraction

When structured skill invocation data exists, use its exact skill identifier. Transcript scanning, when needed, is limited to valid structured tool-call objects within the confirmed agent/session and the checkpoint's registered interval. Narrative references to a skill do not count. Require a unique matched skill within the checkpoint interval and, if present, agreement with `expected_skill`.

Resolve installed skill names from the deployment manifest introduced by spec 13 and/or the corresponding `ORCHESTRAIL_HOME/workflows/*.md` inventory. Do not hard-code a snapshot. Use the actual deployed workflow skill name: do not silently mingle pre- and post-spec-13 names.

If run and checkpoint correlation, outcome, and timing are sound but skill-name identification is genuinely unavailable, **one** `--step unknown` entry may be accepted with `step_name_coverage: unavailable`. Such an entry does not count toward *named-step coverage*. If multiple conflicting skill candidates exist, omit the automatic step rather than pick one.

### 9.2. Strict report marker

A checkpoint report must contain exactly one standalone line of the form:

```text
ORCHESTRAIL_REPORT_V1 checkpoint=cp-red-001 outcome=ok
```

Accept precisely one such marker from the matching agent's last report. Constrain checkpoint identifiers to a documented safe alphabet and maximum length. The outcome must be one of `ok|blocked|failed|skipped|deferred` **without** interpreting aliases from untrusted prose. Do not derive the outcome from `DONE`, `NEEDS WORK`, ordinary prose, a hook exit code, or file existence. Missing, duplicate, conflicting, or invalid markers mean `outcome-unavailable` and **no automatically accepted step**.

An agent can report an incorrect result despite producing a syntactically valid marker. `outcome_source: agent-report` records this provenance; independent `gate` and `tests` fields remain distinct and are never inferred by the hook.

### 9.3. Boundary-observation matrix

| Scenario | Start evidence | End evidence | Required handling |
|---|---|---|---|
| One skill, one subagent, one checkpoint | Envelope plus structured invocation | Bound `SubagentStop` and strict marker | Record one observed step if agent association is verified |
| One agent, two successive reports | Separate envelopes/checkpoints | Two separately bound report stops | Two entries only with two proven boundaries; never reuse a stop |
| Main session, one skill in a turn | Envelope and structured skill call | Matching `Stop` and main-session marker | Close only that checkpoint; otherwise approximate |
| Main session, three skills before a `Stop` | Possibly three starts | Only one response stop | Do not fabricate three ends; uncovered/approximate boundaries remain |
| Nested skill without its own checkpoint | Possibly a start | No trustworthy end | Keep orchestrator fallback and prompt instruction |
| Two parallel subagents in one project | One distinct envelope each | Their own stop events | Require direct agent association; omit ambiguous events |
| Missing stop, marker, transcript path, or start | Partial inputs | Insufficient end/evidence | Coverage warning, no misleading accepted step |
| `hooks: no` or hook inactive for this session | No guaranteed hook evidence | No guaranteed hook evidence | Prompt-driven steps containing `note: approximate` |

## 10. Backward-compatible producer interface

### 10.1. Run mode and coverage closure

Extend `run-start` with optional `--telemetry-mode` values `prompt-only|hook-candidate|unavailable`. Preserve legacy calls without the flag; their measurement mode is unknown. `hook-candidate` is **not** a coverage claim. For a harness without hooks, the orchestrator explicitly uses `--telemetry-mode prompt-only`.

Extend `run-end` with optional `--coverage-from-dispatch`: for its explicit run ID, it reads **only** that run's local active correlation inventory under `~/.config/orchestrail/runtime/runs/<run-id>/`, validates counts, and embeds `measurement_coverage` in the closing record. It cannot accept an arbitrary inventory path. Missing, inconsistent, or incomplete inventory yields `partial` or `unavailable` with a stable reason, and must not prevent an otherwise valid run close. `complete` requires a known expected-checkpoint denominator.

```bash
RUN_ID=$("$LOG_HELPER" run-start --pipeline spec-run \
  --telemetry-mode hook-candidate)
# ... dispatch and work ...
"$LOG_HELPER" run-end --run "$RUN_ID" --outcome completed \
  --coverage-from-dispatch
```

The orchestrator still calls both run boundaries. The producer, canonical rule, runtime contract export, linter, and retrospective must accept the new fields **in the same change**. Legacy closes without the flag remain valid.

### 10.2. Prompt-driven step compatibility

```bash
scripts/log-step.sh step --run 4305eda1 \
  --step atomic-execution-tests --outcome ok --note "approximate"
```

The existing call remains valid. Its `duration_s` is an **approximation based on previous accepted-event timestamps**, not a precise skill interval. If a checkpoint envelope exists, a prompt-side call must include `--checkpoint-id` and use the same once-per-checkpoint guard. Legacy calls without an envelope remain supported for compatibility, but cannot be represented as cross-source deduplicated observations.

For fallback runs, retain any existing user note and append the **literal** text `approximate` using the documented `; ` separator.

### 10.3. Optional measured-step arguments

```bash
scripts/log-step.sh step \
  --run 4305eda1 --step atomic-execution-tests --outcome ok \
  --session-id sess-A --agent-id agent-17 \
  --dispatch-id d-6b3f9c52 --checkpoint-id cp-red-001 \
  --delivery-id h-28d4bc61e6e5763877c8bf6c24b1d2c0d8ee19be5ed76901541362b8121b82cb --delivery-id-source derived \
  --started-at-ms 1792656000000 --ended-at-ms 1792656030000 \
  --start-mono-ns 101000000000 --end-mono-ns 131000000000 \
  --clock-domain host-boot-A \
  --measurement-source hook --outcome-source agent-report
```

Validate new arguments as **one atomic unit**: required companion fields, strict identifier grammar, `--dispatch-id` and `--delivery-id` as **different identities**, `--delivery-id-source harness|derived`, exact nonnegative decimal wall-clock milliseconds and monotonic nanoseconds within a documented bounded integer grammar, `ended-at-ms >= started-at-ms` for an unambiguous wall timeline, `end-mono-ns >= start-mono-ns`, identical verified `clock_domain`, envelope agreement, and allowed source enums. Both monotonic endpoints and the clock domain are mandatory for `measurement-source=hook` measured durations. Accept the exact decimal CLI syntax `0|[1-9][0-9]*` for each nanosecond endpoint, bounded to the **signed 64-bit maximum `9223372036854775807`**; store monotonic endpoints as **JSON decimal strings**, not numbers, to avoid IEEE-754 precision loss after approximately 104 days of uptime. Parse and subtract with exact integer arithmetic, never floating-point JSON arithmetic. Wall milliseconds and derived durations retain spec 02's safe numeric bounds. A wall-clock jump may produce `ended-at-ms < started-at-ms`; then mark the wall timeline unreliable rather than rejecting a valid same-domain monotonic duration, and omit any wall-derived ordering assertions. Never substitute current time for a missing start, convert a negative monotonic interval to zero, or use `last_epoch` as a measured start. Any incomplete or inconsistent required monotonic set rejects the **entire** measured event before mutation.

An accepted measured record retains the existing required fields (`event`, `ts`, `seq`, `pipeline`, `flow`, `run_id`, `step`, `outcome`, `duration_s`) and adds conditionally required **measured-record** fields `session_id`, `agent_id`, `dispatch_id`, `checkpoint_id`, `delivery_id`, `delivery_id_source`, `start_wall_ms`, `end_wall_ms`, `start_mono_ns`, `end_mono_ns`, `clock_domain`, `duration_ms`, `measurement_source`, `outcome_source`; optional fields include `timing_scope`, `parent_checkpoint_id`, `coverage_status`, and `wall_timeline_status: consistent|skewed|unavailable`. The old ambiguous `event_id` field is **not** introduced. `start_mono_ns` and `end_mono_ns` are required **decimal-string** JSON values for measured records, and producer-side run monotonic endpoints use the same representation. Compute `duration_ms = floor((end_mono_ns - start_mono_ns) / 1000000)` and `duration_s = floor((end_mono_ns - start_mono_ns) / 1000000000)` from the **same monotonic delta**. Persist both endpoints and their domain so `/retro` can verify this arithmetic after active state cleanup. Use the unrounded monotonic delta for exact interval boundaries when available, then milliseconds for legacy reporting; wall-clock differences never override it. Extend `lint` to check the new fields, their mathematical consistency and the conditional presence requirements. A wall jump produces `wall_timeline_status: skewed` and disables claims about wall-time placement, but does not invalidate otherwise comparable monotonic elapsed time.

In spec 03, prefer a protected producer write path that verifies a correlated envelope/receipt when `measurement-source=hook`. The caller-supplied flag by itself does not upgrade an observation to trusted measured status.

### 10.4. Atomicity and concurrency

1. The hook prechecks project scope and payload. **The producer remains the final validation authority** and validates the complete supplied argument set before active metadata, accepted receipts, sequence, or history mutation.
2. For a validated checkpoint, the **producer itself** acquires a bounded, per-run lock. `run-end` uses the same lock to serialize closure against late step events. Failure to acquire emits a warning and safely omits telemetry. Do not recursively acquire the producer's lock in its calling wrapper.
3. Under that lock, reverify the active run, envelope, checkpoint ownership, dispatch identity, delivery identity/source, both monotonic endpoints with the same clock domain, authorized worktree, receipt state, and absence of an accepted run close.
4. Reserve a once-only checkpoint key with race-safe exclusive creation (`O_EXCL` or equivalent). Competing deliveries observe `duplicate` and append nothing.
5. Apply existing JSONL/sequence persistence checks, then mark the receipt accepted **only after** the write is confirmed. Unprovable success is `uncertain`, not accepted. Do not blindly replay a reserved key.
6. If interrupted between reservation and acknowledgment, mark the checkpoint `uncertain` on the next attempt and report partial coverage. The hook cannot inspect historical JSONL to guess whether the append occurred.

**Guarantee boundary:** Without one shared filesystem transaction, it is impossible to guarantee exactly-once effects across a crash while forbidding historical recovery reads. Spec 03 chooses **at most one accepted checkpoint event**, with explicit uncertainty and no blind retries. Spec 02's existing partial-filesystem-write caveat remains; `lint` must detect corrupt lines. The same lock protects receipts and append invariants. Invalid invocations must never reserve a key.

`seq` is the order of **accepted writes**, not necessarily event-time order. Sort measurement intervals by start/end during aggregation. After a physically accepted `run-end`, a late `SubagentStop` emits `late-event` coverage diagnostics and never reopens history.

## 11. Claude Code hook adapter

### 11.1. Manifest and event semantics

`harness/claude/hooks.json` **must** declare `SubagentStop` and `Stop` command hooks invoking `hooks/log-step-hook.sh`. Optional `SessionStart`, `SubagentStart`, and `PreToolUse` restricted to `Skill` may be used solely to obtain structured session/agent identity or start evidence, when verified on the deployed harness version. `PreToolUse: Skill` is **not** proof that a workflow step has ended; unsupported auxiliary events must not be silently replaced with fictional observations.

Proposed manifest (commands point to a **user-level installed copy**, never a consumer repository):

```json
{
  "hooks": {
    "SessionStart": [
      {"matcher": "", "hooks": [
        {"type": "command", "command": "bash \"$HOME/.config/orchestrail/hooks/log-step-hook.sh\" session-start"}
      ]}
    ],
    "PreToolUse": [
      {"matcher": "Skill", "hooks": [
        {"type": "command", "command": "bash \"$HOME/.config/orchestrail/hooks/log-step-hook.sh\" skill-start"}
      ]}
    ],
    "SubagentStart": [
      {"matcher": "", "hooks": [
        {"type": "command", "command": "bash \"$HOME/.config/orchestrail/hooks/log-step-hook.sh\" subagent-start"}
      ]}
    ],
    "SubagentStop": [
      {"matcher": "", "hooks": [
        {"type": "command", "command": "bash \"$HOME/.config/orchestrail/hooks/log-step-hook.sh\" subagent-stop"}
      ]}
    ],
    "Stop": [
      {"matcher": "", "hooks": [
        {"type": "command", "command": "bash \"$HOME/.config/orchestrail/hooks/log-step-hook.sh\" stop"}
      ]}
    ]
  }
}
```

Installation must verify the actual event names and usable fields on the target Claude Code version. Missing support for an auxiliary event disables only its dependent evidence; the two required stop declarations remain. Observations that require unavailable evidence revert to the safe fallback. The adapter must not emit blocking JSON, request a stop, or return exit code `2`.

### 11.2. Fast project guard

In `hooks/log-step-hook.sh`, **before consuming stdin JSON**, running expensive tools, or reading envelopes:

1. Resolve the physical hook working directory with `pwd -P`. Check that the registry `~/.config/orchestrail/projects` is present/readable. Canonicalize its registered roots, rejecting missing or untrusted paths. Do not read the hook's stdin payload or correlation envelopes yet.
2. Fast path: permit the directory if it equals a registered physical root or is its descendant at a **path-component boundary**, never by naive string prefix.
3. Linked-worktree path: if not on the fast path, resolve the candidate Git worktree top level and its physical path. Independently enumerate **Git's registered linked worktrees** with `git -C <trusted-registered-root> worktree list --porcelain -z` (or an equivalently machine-safe format). Require an exact canonical top-level path match in that trusted enumeration, the hook `pwd -P` to lie within that matched worktree, and an exact match between the candidate's resolved Git common directory and the trusted registered root's Git common directory. An unlisted checkout, a repository sharing a remote URL, a copied `.git` file, and a lookalike path are not authorized. Handle spaces, newlines, absent Git, malformed registry entries, and stale worktree listings by safely skipping; bound enumeration work to registered roots without scanning the filesystem.
4. Only after either path is verified may the adapter read its bounded JSON payload. Canonicalize the payload `cwd` and require it to match the physical invocation directory (or a target-version-verified equivalent within the **same** authorized worktree). Validate that an optional `CLAUDE_PROJECT_DIR` points to the registered original root; it is a **hint**, never authority. In a linked worktree, `cwd` may name the worktree while `CLAUDE_PROJECT_DIR` names the original root; this valid difference must **not** cause rejection.
5. After explicit envelope lookup, require `project_realpath` to equal the verified registered original root and `worktree_realpath` to equal the verified active checkout root. Reject mismatches and missing authorization before any log write. Worktree listing alone is **not** dispatch/run attribution.

Reject symlink escapes, fake/unlisted linked worktrees, and similarly prefixed sibling paths. An absent/unreadable registry or unmatched directory/worktree yields immediate silent exit `0` with no state changes or payload reads. Valid linked worktrees still need an envelope explicitly authorizing that checkout; do not treat `CLAUDE_PROJECT_DIR`, a common Git remote, or a Git common directory alone as run attribution.

Bound processing time and input size with documented constants tested offline. Never read entire transcripts or fetch anything over the network. A missing dependency (for example, `python3` or JSON parser), corrupt envelope, or parse failure emits a safe warning **only after** project verification and returns `0`. Avoid stdout responses that could change hook behavior or recursively cause additional hook events.

### 11.3. Manifest-owned user settings merge

`scripts/sync.sh`, driven by `harness/<name>/deploy.env` and optional `hooks.json`, installs the executable hook at `~/.config/orchestrail/hooks/` and merges **only manifest-owned entries** into the user's `~/.claude/settings.json`. Never install a project-level hook or commit a hook into a consumer repository.

Compare hook entry structures by `(event, matcher, type, command)` and maintain a separate user-level installation ownership manifest that lists the exact entries actually installed. Do **not** assume Claude Code supports an arbitrary `id` property in its settings schema.

Preserve all unrelated settings, third-party hook groups and entries in their existing relative order. Running sync twice produces exactly one instance of each managed entry. A newer manifest may replace only an unambiguously owned previous entry. A manually edited entry is treated as user-owned and cannot be silently removed. An explicit `sync.sh --uninstall-hooks` removes only exact matching owned entries.

Invalid/unreadable settings must remain byte-for-byte unmodified; installation reports a safe warning and telemetry uses the approximate fallback. Write through a temporary file in the same directory and atomic replacement while retaining permissions; create a backup before the first actual replacement. Detect concurrent user edits and abort rather than overwrite them. A settings entry **alone** is never proof that a hook executed in the current session.

## 12. Per-boundary selection in workflows

Apply this decision tree at **every expected boundary**:

1. Read declared `hooks` capability from spec 13's deployed always-on capability table and supply a matching `--telemetry-mode` to `run-start`. For `no` or unsupported/unknown capability, retain each prompt-driven `step` call with `note: approximate`.
2. For `yes`, verify that an explicitly correlated dispatch envelope and a current-session hook signal are actually obtainable. `yes` does not by itself permit prompt removal.
3. Only for independently proven boundary classes, register the checkpoint before dispatch and let the hook perform the immediate step write. Remove the duplicate model prompt **only for those specific boundaries**.
4. Retain prompt-side approximate logging for unobservable boundaries and report uncovered checkpoints separately.
5. Finalize the expected-checkpoint inventory and invoke prompt-driven `run-end --coverage-from-dispatch`. If the inventory is absent, coverage is `unavailable`, not complete.

Audit the current `workflows/phase-*` family, the future spec-13 names (`discovery/*`, `execution/*`, `validation/*`, `atomic-*`), and `workflows/spec-run.md` in the actual post-spec-13 tree. Synthetic `subtask`, `batch-gate`, and `dry-run` steps, orchestration loops, and internal handoffs do **not** automatically correspond to a completed skill.

`/spec-run` uses RED and GREEN checkpoints for one Implementer agent. Each intermediate report requires its own identity; one `SubagentStop` cannot simultaneously finish `tests`, `implement`, and `finalize`. If boundaries are not independently observed, preserve existing orchestrator-owned approximate prompts.

For `hooks: no`, every newly produced `step` line must contain the literal `approximate` in `note`; preserve any existing note using `; `. `/retro` must label those observations as approximate. Unknown effective hook support selects the same safe fallback, never a measured label inferred from legacy timestamps.

## 13. Timing model and denominators

### 13.1. Clock and measurement sources

Prompt-driven `run-start`/`run-end` provide producer-stamped run boundaries. To prevent precision loss, persist all absolute monotonic nanosecond endpoints as base-10 JSON strings (`"0"` or a non-zero digit followed by digits), bounded to signed 64-bit integers; validate them with exact integer arithmetic and check differences before narrowing to existing spec 02 bounded `duration_ms` and `duration_s` integers. Each measured checkpoint **must** carry `start_wall_ms`, `end_wall_ms`, `start_mono_ns`, `end_mono_ns`, and a verified `clock_domain` identifying one comparable monotonic clock (for example, a host boot identity and clock type). The monotonic samples must be taken at the corresponding dispatch/start and correlated stop boundaries; do not use timestamps supplied by the agent's text. For a measured span, calculate elapsed duration **only** as the same-domain monotonic difference. A clock-domain mismatch, missing endpoint, or reversed monotonic endpoint makes measured timing `unavailable`, not zero or wall-derived.

`duration_ns = end_mono_ns - start_mono_ns`, `duration_ms = floor(duration_ns / 1000000)` and `duration_s = floor(duration_ns / 1000000000)`. Preserve both raw monotonic endpoints and domain in the historical measured record. Use the monotonic delta (not independently rounded milliseconds or seconds) for overlap/gap comparisons among spans sharing that clock domain. Wall timestamps provide calendar placement only when reliable: if wall-clock movement differs from comparable monotonic movement by more than a documented tolerance (default fixture threshold **1000 ms**), label `wall_timeline_status: skewed` and omit exact wall-based placement. Even an otherwise correct monotonic duration cannot establish an exact position in a skewed wall-clock run timeline.

For the **run wall** denominator, take producer-side monotonic readings at both prompt-driven boundaries when the installed runtime exposes a comparable domain, and persist `run_start_mono_ns`, `run_end_mono_ns`, `run_clock_domain`, and derived `run_wall_ms` on the accepted `run-end`. These are additive and must preserve legacy integer `run-end.duration_s` semantics; `/retro` prefers the reliable `run_wall_ms` for precise coverage ratios. When such comparable run endpoints are absent, existing producer-stamped epoch wall time is labeled `approximate` and a detected clock discontinuity makes the precise run-wall denominator `unavailable`; do not claim the 5% fixture target from unreliable wall time. Across devices/hosts or incompatible domains, the relevant difference and cross-span union are unavailable, not inferred. Observed elapsed intervals can include waiting/scheduling; active model compute time remains unavailable without a separate signal.

### 13.2. Disjoint metrics

Let `I_i = [s_i, e_i)` be observed spans, and `R = [r_s, r_e)` the run interval:

- `inclusive_ms(i) = e_i - s_i`.
- `child_union_ms(i)` is the measure of the union of *confirmed* direct and indirect descendant spans, intersected with `I_i`.
- `exclusive_observed_ms(i) = inclusive_ms(i) - child_union_ms(i)` measures time outside observed descendants; it **may still include waiting** and is not pure compute time.
- `worker_sum_ms` is the sum of inclusive durations over a **specified set of worker leaves**; parallel workers contribute effort, not additive run wall time.
- `covered_union_ms` is the union of eligible observed spans clipped to `R`.
- `uncovered_gap_ms = wall_ms - covered_union_ms` when `R` and the relevant observed spans are known; otherwise report partial/unavailable coverage and unknown missing boundaries.
- `overlap_ms = sum(inclusive_ms) - union_ms` for an explicitly named span set. Nesting may contribute multiplicity.
- `waiting_ms` is measurable **only** from independently observed waiting spans; otherwise display `waiting: unavailable`, not `0`.

For sequential runs, check that adjacent observed step intervals do not overlap and explicitly enumerate the before-first, between-steps, and after-last gaps. The requested **within 5%** condition is tested **only** on a fixture declared sequential and fully inventoried, never used to stretch or adjust measurements:

`abs(wall_ms - sum(inclusive_ms)) / wall_ms <= 0.05` for `wall_ms > 0`.

Label gaps even if their combined duration is under 5%. A real sequential run with more than 5% uncovered time honestly fails the completeness target; do not hide the discrepancy.

### 13.3. Hand-verifiable fixtures

**Sequential:** On one comparable monotonic domain, `R = [0,100000)` ms; steps `[0,30000)`, `[30000,70000)`, `[70000,98000)`. Inclusive sum `98000` ms; coverage `98%`; gap `[98000,100000)` = `2000` ms; overlap `0`; difference `2%`, meeting the 5% fixture condition. Add a forward wall-clock jump of `60000` ms during the second step: step duration stays `40000` ms from monotonic endpoints, while exact wall timeline is flagged skewed.

**Nested:** Parent `[0,100000)`, child `[20000,60000)`. Parent inclusive `100 s`, child inclusive `40 s`, parent observed exclusive `60 s`. Inclusive sum `140 s` **is not** run wall `100 s`. Waiting without a distinct signal is unavailable.

**Parallel:** Two independent workers `[0,50000)` each; `R = [0,50000)`. Worker sum `100 s`, covered union `50 s`, overlap `50 s`, run wall `50 s`. Never report "run time: 100 s".

**Partial:** One known worker span `[10000,30000)`; another worker's end is missing. Do not include the unknown span in measured-duration totals. A closed run does not make step coverage 100%; missing intervals cannot be assigned to the unknown worker.

## 14. Coverage inventory, diagnostics, and retrospective

Track **expected** checkpoints, not just delivered events. Each checkpoint carries minimal machine-readable status from `expected`, `observed`, `approximate`, `uncovered`, `ambiguous`, `duplicate`, `late`, `invalid`, or `uncertain`. These are **coverage metadata**, not new `step.outcome` values. The historical measured step retains separate `dispatch_id` and `delivery_id` fields, their delivery source, monotonic endpoints/domain, and wall timeline quality, so provenance and duration remain auditable after active metadata cleanup.

At a minimum, persist the following additive object in an accepted `run-end`:

```json
{
  "measurement_coverage": {
    "status": "partial",
    "expected_checkpoints": 4,
    "observed_checkpoints": 2,
    "approximate_checkpoints": 1,
    "uncovered_checkpoints": 1,
    "unknown_inventory": false,
    "reasons": ["missing-outcome-marker"]
  }
}
```

Allowed coverage status is `complete|partial|unavailable`. Completeness requires a known expected-checkpoint denominator and no declared unobserved boundaries. A correlated step recorded as `step: unknown` may have a measured duration but does not contribute to *named-step* coverage; show time coverage and name coverage separately.

Only `/retro` performs **analytical** reads and aggregation of the historical shared store. The producer may continue its **existing own-file append checks and run-end digest generation**; this is a narrow backward-compatibility exception, not permission for the adapter or live workflows to search historical logs. If "only `/retro` may read any `.jsonl` bytes" is later interpreted literally, changing the digest implementation requires a separate compatible decision.

`/retro` lints its selected file corpus, excludes invalid lines, and separately reports runs, observed steps, approximate steps, uncovered checkpoints, unknown inventories, incomplete closes, and uncertain writes. Median duration samples must identify their series: confirmed observed spans versus separately labeled approximate spans. Treat older records without measurement provenance as approximate/unknown, **not** observed. Missing physical `run-end` remains an abandoned run; a physically present but invalid end remains an unusable close, per spec 02.

Emit one short warning per detected adapter problem, containing a stable code, field name, and optionally a safe checkpoint identifier. Never echo arbitrary input values, raw transcript excerpts, message text, secrets, or paths to private source files. Persist aggregate reason codes in active coverage state where attribution is already proven. Telemetry errors must not block work or produce success-shaped fabricated events.

## 15. Failure and security matrix

| Condition | Required behavior |
|---|---|
| Working directory outside the registry | Immediate silent exit; do not read payload, envelope, or history |
| Two runs in one project/session | Direct dispatch/checkpoint correlation only; do not mutate the other run |
| Absent, corrupt, or stale envelope | `attribution-unavailable`; no active-run guessing |
| Unbound `agent_id` | `ambiguous-agent`; do not use `agent_type` as a substitute |
| Missing/duplicate/conflicting marker | `outcome-unavailable`; no automatic step |
| No structured skill identifier | `unknown` only with proven run/checkpoint and other required evidence; otherwise omit |
| One stop after multiple skills | Never invent multiple exact closes; retain uncovered/approximate boundaries |
| Replayed stops from two channels | One receipt per checkpoint and at most one accepted event |
| End before start or incomparable clocks | `timing-unavailable`; do not record a fabricated zero |
| `run-end` accepted before delayed stop | Skip late event; report partial coverage; never rewrite history |
| Missing permissions, JSON parser, or other dependency | Exit `0`, safe warning, approximate/unavailable fallback |
| Invalid `settings.json` | Preserve user bytes; hooks effectively unavailable |
| Symlink escaping project or state root | Deny access and skip logging |
| Valid Git-linked worktree of registered project | Verify trusted `git worktree list` membership, common Git directory, canonical `cwd`, and envelope's `worktree_realpath`; then permit |
| Forged `CLAUDE_PROJECT_DIR` or unlisted/mismatched worktree | Never trust environment alone; immediate silent exit or coverage unavailable without mutation |
| Missing/mismatched monotonic endpoint or domain | No measured duration, even if wall-clock times exist |
| Wall clock jumps while monotonic clock remains stable | Persist correct monotonic elapsed duration and `wall_timeline_status: skewed`; exact wall placement unavailable |
| Reused dispatch ID as hook delivery identity | Reject invalid identity contract; keep separate dispatch and delivery fields |
| Crash during append/receipt update | Mark `uncertain`, never blindly append again |
| Unsupported auxiliary hook on target version | Dependent boundary proof unavailable, never claim exact observation |

A report marker does not authorize external actions. The adapter runs under the local user's ordinary permissions and must not request elevated privileges. Every path derived from hook input must be constrained to the previously established session/project scope.

## 16. Model-free executable fixtures

Use disposable `mktemp` directories and temporary `HOME`, `ORCHESTRAIL_HOME`, `ORCHESTRAIL_LOG_ROOT`, registry, and copies of installation files. Tests submit synthetic JSON events on stdin and inspect only isolated JSONL, receipts, coverage inventories, and reports. Do not invoke models, access the network, or touch real user settings or logs. Clocks must be injectable, avoiding sleeps and wall-time assertions.

| Test | Fixture | Mandatory assertion |
|---|---|---|
| **T-01** | Registered/unregistered directories, path prefixes/symlinks, valid linked worktree, unlisted worktree, copied `.git`, forged `CLAUDE_PROJECT_DIR`, and payload `cwd` differing from registered main root | Registered root and verified explicitly authorized linked worktree work; all unregistered/forged cases read no payload or mutate no log; exit `0` |
| **T-02** | Interleaved runs A and B in one project, agents 1 and 2 | Exact run/checkpoint attribution; other run's bytes and metadata unchanged |
| **T-03** | Foreign `run_id` in agent's final prose | Ignore text; correlate only using envelope |
| **T-04** | Multiple active runs; no dispatch association | No automatic event; explicit attribution warning |
| **T-05** | Duplicate `SubagentStop`, `Stop`, conflicting repeated outcome, distinct hook delivery IDs for one dispatch | One accepted `step`; no extra sequence/timestamp advance; historical record contains separate correct `dispatch_id` and accepted `delivery_id` even after active-state deletion |
| **T-06** | Stop before start; late stop after `run-end` | No negative duration or post-close append; uncovered status |
| **T-07** | Missing agent/session/marker/start/transcript or either monotonic endpoint/clock domain | Correct partial/unavailable response; never mutate other run; wall-clock-only data cannot masquerade as measured |
| **T-08** | One exact marker, two markers, `DONE` prose, bad outcome | Only a single valid strict marker is accepted |
| **T-09** | Structured `Skill`, narrative skill mention, envelope mismatch | Structured name only; mismatch not attributed |
| **T-10** | One skill in a main session with explicit envelope | `Stop` closes just that point; trusted source identified |
| **T-11** | Three skills in main session before one `Stop` | No three invented measured closes; coverage incomplete |
| **T-12** | Unknown name with proven vs. unknown run | `unknown` permitted only in proven correlation; otherwise no event |
| **T-13** | `hooks: no`; `hooks: yes` but no current-session signal | Fallback `note` literally contains `approximate`; `/retro` splits series |
| **T-14** | Same Implementer, separate RED and GREEN checkpoints | Distinct keys; one stop does not close two checkpoints |
| **T-15** | Parallel agents with no common binding key | No "single pending agent" heuristic |
| **T-16** | Parallel duplicate deliveries within a run | One receipt and one accepted sequence per checkpoint; serialized write |
| **T-17** | Faults at reservation, append, acknowledgment, cleanup | `uncertain` where needed, at most one accepted event, exit `0` |
| **T-18** | Invalid new step args, types, empties, duplicate flags, swapped `dispatch_id`/`delivery_id`, reversed monotonic endpoints, mismatched clock domains, malformed/overflowed nanosecond decimal strings, and values beyond the signed 64-bit bound | Spec 02 invariant: no log/`seq`/`last_epoch`/accepted-receipt mutation; large valid nanosecond strings above `2^53` remain exact |
| **T-19** | Legacy and new entries under `lint`, including monotonic/wall jumps, absolute nanoseconds above `2^53`, and persisted dispatch/delivery provenance | Backward compatibility; exact integer-string monotonic `duration_ms`/`duration_s` verified without floating-point rounding, missing or inconsistent new fields reported, stable duration with skewed wall timeline identified |
| **T-20** | Reinstall/uninstall with unrelated hook entries and settings | Idempotent ownership-only edits; preserve other settings |
| **T-21** | Corrupt settings JSON; concurrent manual settings edit | No overwrite; safe fallback |
| **T-22** | Sequential fixture from §13.3, with comparable monotonic domains and a forward wall-clock jump | 98% coverage, 2% gap, 0 overlap, within 5% by monotonic run wall; a forward wall jump does not inflate measured elapsed time |
| **T-23** | Nested fixture from §13.3 | Parent/child inclusive 100/40s, parent exclusive 60s, sum 140s vs wall 100s |
| **T-24** | Parallel fixture from §13.3 | Worker sum 100s, union 50s, overlap 50s, wall 50s |
| **T-25** | Four expected points: 2 observed, 1 approximate, 1 uncovered | 2/4 observed, `partial`; unknown inventory not called complete |
| **T-26** | Full existing acceptance and contract suite | `bash tests/log-step.sh`, `bash scripts/validate-contracts.sh`, `bash -n` on changed shell scripts all pass |

Snapshot/hash guards must verify that no test touched actual `logs/runs/`. Run the tests under temporary source and log roots, including both successful and failed writes. These fixtures cannot replace the target-version compatibility check in REQ-20; that check must not require a paid model experiment for ordinary acceptance.

## 17. Acceptance criteria

- [ ] **AC-01 (REQ-01, 02, 03, 06, 07).** Interleaved two-run fixtures attribute by explicit envelopes. An ambiguous stop mutates neither run; invoked skill and reported outcome have verifiable sources. An accepted historical step carries distinct `dispatch_id` and `delivery_id`, even after active correlation state is removed.
- [ ] **AC-02 (REQ-05, 08, 09, 16).** Duplicates/races never produce two accepted events. Invalid data leaves `seq`, `last_epoch`, active metadata, and receipts unchanged. Late events never rewrite a closed run.
- [ ] **AC-03 (REQ-10, 11, 19, 20).** `harness/claude/hooks.json` declares `SubagentStop` and `Stop`; the hook is inert outside registered projects and securely validated, explicitly dispatched linked worktrees; repeated installation and targeted uninstall preserve unrelated user settings. A forged `CLAUDE_PROJECT_DIR` grants no access.
- [ ] **AC-04 (REQ-04, 12, 13, 14).** Missing capability/payload and single-session multi-skill execution cannot report false complete coverage; every prompt fallback step includes `note: approximate`; orchestrator owns `run-start` and `run-end`.
- [ ] **AC-05 (REQ-04, 15, 18).** Sequential fixture reports 98% observed coverage and a labeled gap. Nested/parallel fixtures report inclusive, observed exclusive, union, worker sum, overlap, and wall time separately. Both monotonic endpoints and the common domain survive in measured history; a wall-clock jump does not inflate elapsed time.
- [ ] **AC-06 (REQ-17, 19).** All offline fixtures and existing gates pass without model calls. Adapter errors always return `0` and do not access other logs.
- [ ] **AC-07 (REQ-09, 14, 18).** `rules/run-log.md`, adapter contract, `lint`, `/retro`, and vocabulary validator agree. New run mode and coverage flags are validated; old valid rows remain valid and old histories are unchanged.
- [ ] **AC-08 (REQ-12, 13).** Remove orchestrator per-step logging prompts **only** for boundaries demonstrably observed by fixtures. Unobserved `subtask`, `batch-gate`, `dry-run`, and internal boundaries keep approximate or uncovered treatment.

## 18. Traceability

| Requirements | Acceptance | Tests |
|---|---|---|
| REQ-01–03, 06–07 | AC-01 | T-02–04, T-08–09, T-12, T-15 |
| REQ-05, 08–09, 16 | AC-02 | T-05–07, T-16–19 |
| REQ-10–11, 19–20 | AC-03, AC-06 | T-01, T-20–21, T-26 |
| REQ-04, 12–14 | AC-04, AC-08 | T-06–14, T-25 |
| REQ-15, 18 | AC-05, AC-07 | T-19, T-22–25 |
| REQ-17 | AC-06 | T-01–26 |

## 19. Proposed implementation slices

**Slice 1 — Contract and fixtures.** Freeze versioned envelope schema, strict report marker, boundary matrix, failure semantics; implement failing T-01–15 first. Add arithmetic goldens T-22–25.

**Slice 2 — Producer compatibility.** Add correlated optional interval arguments, receipts, same-run serialization, validation and lint without regressions to spec 02. Stabilize T-05–07 and T-16–19.

**Slice 3 — Hook and dispatch adapters.** Implement `hooks/log-step-hook.sh` and the prepare/bind envelope operations; prove skill/matcher provenance, two simultaneous runs, and absence of unsafe agent heuristics. Explicitly mark unsupported boundaries.

**Slice 4 — Capability-aware installation.** After spec 13 lands, add `harness/claude/hooks.json`, registry guard, targeted settings merge/uninstall and preservation fixtures.

**Slice 5 — Workflows and retrospective.** Audit each boundary, remove prompts only where demonstrated, retain approximate paths, persist coverage on close, report separate time denominators, and update canonical `rules/run-log.md` together with producer and `/retro`.

**Slice 6 — Independent verification.** Run offline regression/contract/syntax checks and inspect hook payload support in an installed compatible Claude Code version without paid experiments; publish the exact supported boundary inventory.

Local test-first commits are allowed under existing repository policy. This design does not authorize merging, paid runs, or expanding scope.

## 20. Risks and accepted tradeoffs

| Risk | Mitigation |
|---|---|
| No common machine-readable identity between dispatch and `agent_id` | Do not claim automatic coverage; use a proven later binding or approximate path |
| Stop event does not align with skill completion | Checkpoint-specific eligibility; never assume one stop closes all skills |
| Agent returns a syntactically correct but false outcome | Explicit `outcome_source: agent-report`; independent verification stays separate |
| Crash between write and receipt | Prefer at-most-one accepted event and disclosed uncertainty to blind replay |
| No shared monotonic clock across hosts | Duration unavailable, with explicit clock provenance |
| System wall clock jumps while steps run | Monotonic endpoints determine elapsed time; wall timeline marked skewed and incompatible coverage denominators withheld |
| Registered project uses sibling worktrees | Trust Git's linked-worktree inventory plus canonical paths and explicit per-dispatch worktree authorization; never trust `CLAUDE_PROJECT_DIR` alone |
| Dispatch ID confused with delivered hook event identity | Distinct producer flags and persisted fields; acceptance deduplicates by run/session/checkpoint, not delivery ID |
| Pre-/post-spec-13 skill names differ | Derive names from actual installed manifest, never invented aliases |
| User-level settings are shared and user-owned | Ownership manifest, exact structural merge/removal, atomic write |
| Retrospective confuses overlapping duration metrics | Distinct denominators and coverage, never sum overlapping spans as wall time |

## 21. Assumptions, verification gates, and readiness

These are **technical prerequisites to verify**, not permission to guess:

1. Verify the installed Claude Code version and actual structured fields available for `Skill`, subagent startup, and binding a dispatch result to `agent_id`. Until proven, declare only partial coverage; fixture input supplies identities explicitly.
2. Once spec 13 lands, enumerate deployed skill names from its actual manifest. Build the boundary map from that state, not from historical names in the present repository. Verify registered linked-worktree enumeration, canonical worktree roots, and matching dispatch envelope scopes under both sequential and `--parallel` operation.
3. Reconcile the phrase "only `/retro` reads the shared log store" with the existing producer that reads its own file for append checking and digest generation. This spec prohibits **attribution/analytics reads** by the hook or live workflows while preserving existing producer operations. A literal no-read-anywhere interpretation requires a separate compatible digest decision.
4. Coverage is persisted in the accepted closing `run-end` via `--coverage-from-dispatch`. A run without an accepted close therefore has no proven final inventory; `/retro` must say so. A separate live-incomplete-run coverage interface, if needed, requires an additive contract and must not be silently improvised.
5. Specify monotonic clock acquisition for the supported operating systems and test that `clock_domain` denotes a genuinely shared monotonic timescale; absence of both comparable ends disables measured duration. Store independent producer-side run-boundary monotonic evidence if precise run wall coverage is claimed.

**Readiness:** requirements, source evidence, per-boundary coverage, safe degradation, and model-free tests are specified. Implementation is gated by spec 13 and demonstrated identity binding on the target harness. No paid model execution is needed for the offline acceptance suite.

## 22. References

- Repository: <https://github.com/AlekseiChirkov/agentic-workflows>.
- Original spec 03: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/.ai/specs/03-hook-based-logging.md>.
- Completed spec 02: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/.ai/specs/completed/02-run-log-vocabulary-validation.md>.
- Spec 13: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/.ai/specs/13-model-only-harnesses-and-rule-naming.md>.
- ADR-0009: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/.ai/adr/0009-task-unknown-roadmap-decisions-2026-09.md>.
- ADR-0011: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/.ai/adr/0011-task-02-run-log-contract.md>.
- Canonical run-log rule: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/rules/run-log.md>.
- Current producer: <https://github.com/AlekseiChirkov/agentic-workflows/blob/main/scripts/log-step.sh>.
- Claude Code hook reference: <https://code.claude.com/docs/en/hooks> and <https://code.claude.com/docs/en/hooks-guide> (reviewed 2026-10-22; verify against the installed target version).
