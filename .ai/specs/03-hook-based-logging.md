# Drive run-log `step` calls from harness hooks

## Goal

Run 4305eda1 logged all twelve steps at run-end with `duration_s: 0`: the model wrote
the log retroactively because nothing forces a call when a step finishes. Claude Code
hooks can record explicitly dispatched checkpoints with executable timestamps. The
workflows retain approximate prompt logging at boundaries the hooks cannot demonstrate
(ADR-0009, Decisions 2 and 5).

## Acceptance Criteria

- [ ] `harness/claude/hooks.json` declares `SubagentStop` and `Stop` hooks that call
      `hooks/log-step-hook.sh`; the script derives the step name from the invoked skill
      (never from model text), the outcome from the agent's report marker, and uses an explicit
      run/session/agent correlation supplied at dispatch. It never guesses the run from
      the newest active timestamp or reads the shared store to attribute an event
- [ ] The hook is installed at **user level** (`~/.claude/settings.json`) by `sync.sh`,
      idempotently and without clobbering existing hooks, and exits immediately unless the
      current directory is in `~/.config/orchestrail/projects`
- [ ] Single-session `/phase-*` runs: steps are detected from the skill name in the
      transcript on a best-effort basis; a step name the hook cannot identify may use
      `step: unknown` only when its run is unambiguously correlated; otherwise the event
      is omitted with a coverage warning, never attached to another run
- [ ] `run-start` / `run-end` stay prompt-driven in the orchestrator workflows; per-step
      logging prompts are removed only for step boundaries reliably observed by the
      hook adapter. `hooks: yes` alone does not prove workflow-step coverage; unobserved
      boundaries retain prompt-driven logging and approximate labels
- [ ] For a harness with `hooks: no` the prompt-driven path remains and
      every step line it writes carries `note: approximate`; `/retro` labels such runs
- [ ] A fully covered sequential fixture reports explicit nonoverlapping intervals whose
      sum is within 5 % of run wall time, with uncovered gaps labeled. Nested/parallel
      fixtures report inclusive/exclusive/worker durations separately; their span sum
      is never equated to run wall time
- [ ] `rules/run-log.md` documents both paths and the capability that selects them

## Out of Scope

- Cost/token fields (spec 05); git rails (spec 06)
- Project-level hook installation (rejected: would be committed with consumer repos)

## Notes

- Decisions: ADR-0009 Decision 2 (capabilities, registry) and 5 (user-level hooks,
  `SubagentStop` + `Stop`, run-start/run-end prompt-driven, Codex approximate).
- Depends on spec 02 (vocabulary) and spec 13 (`harness/` layout, capabilities).
- The hook must be fast and must never fail the tool call it observes.

## Review integration — 2026-10-21

### Requirements

- **REQ-01** THE SYSTEM SHALL correlate run/session/agent/checkpoint identities explicitly,
  deduplicate Stop/SubagentStop delivery and preserve completed spec 02's validation,
  non-blocking diagnostics and no-mutation-on-invalid-input behavior.
- **REQ-02** IF hook payloads lack a reliable run, step, outcome or start time, THEN
  THE SYSTEM SHALL report attribution/coverage unavailable or approximate; it SHALL
  NOT parse narrative prose as a definitive outcome or assign another active run.
- **REQ-03** THE SYSTEM SHALL keep active correlation metadata separate from historical
  event lines and use the explicit dispatch envelope for attribution. The hook adapter
  SHALL NOT read historical event lines to discover a run. Retrospective analysis and
  the read-only linter may read historical events for their documented purposes. Spec
  05 owns usage normalization and cost, not the hook adapter.
- **REQ-04** THE SYSTEM SHALL merge only manifest-owned user hook entries, preserve
  user settings, activate only in registered projects and expose capability-based
  fallback. A generic Stop event SHALL not be assumed to occur at every workflow step.
- **REQ-05** THE SYSTEM SHALL test two concurrent runs in one project, duplicate/
  out-of-order events, missing payloads, single-session boundaries and unavailable
  hooks without invoking a model. Duration claims SHALL distinguish gaps, overlaps,
  waiting and actual exclusive work.

### Acceptance additions

- [ ] **AC-01** (REQ-01, REQ-02, REQ-03) Interleaved two-run fixtures attribute correctly;
  duplicate deliveries cannot create duplicate accepted events and an ambiguous event
  cannot mutate either run.
- [ ] **AC-02** (REQ-04, REQ-05) Hook install/uninstall fixtures preserve user settings;
  absent capability/payload follows the documented prompt-driven approximate path;
  unobserved step boundaries remain explicitly uncovered.
- [ ] **AC-03** (REQ-05) Sequential/nested/parallel timing fixtures expose the specified
  denominators and never present overlapping worker time as run wall time.

These additions refine correlation and timing, not paid-run authorization. Update the
canonical log rule/adapter contract together. Depends on 02 and 13; 05 consumes the
measurements. Remove step prompts only for boundaries demonstrably observed by hooks.

## Resolved interface contract

These choices make the accepted behavior executable. They do not change the product
intent in REQ-01 through REQ-05.

### Dispatch and completion markers

- A workflow calls `hooks/log-step-hook.sh dispatch` with the explicit run ID, a stable
  dispatch actor ID, boundary (`session` or `subagent`), and an expected skill name when
  known. The command reads the current Claude session ID from
  `CLAUDE_CODE_SESSION_ID`, generates a checkpoint ID and millisecond start time, and
  records the canonical project root. Missing run or session identity makes dispatch
  unavailable; it never searches for a recent run.
- A session boundary uses `agent_id` equal to its native `session_id`. A subagent
  boundary uses a stable caller-supplied actor ID; the native subagent transcript binds
  that actor to the actual completion.
- Dispatch records use schema version `1`, are stored as mode `0600` files beneath
  `${XDG_STATE_HOME:-$HOME/.local/state}/orchestrail/hooks/`, and never include
  conversation text. The directory is mode `0700`. Records have a private state of
  `pending`, `delivering`, `accepted`, `fallback`, or `fallback-attempted`.
- Fresh private records and acceptance receipts require canonical decimal integer
  tokens for timestamps and sequence numbers, validated from raw JSON before numeric
  conversion. Reject fractional, negative and exponent encodings even if jq rounds
  them to an integer. Schema version uses the exact integer token `1` in private
  records and report/dispatch markers. Historical lint's mathematical integer
  compatibility does not broaden this fresh protocol. Invalid cached timestamps or
  receipts cannot forward delivery, return accepted status or mutate accepted state.
- Dispatch prints one compact, key-sorted line for the workflow to include unchanged in
  the dispatched agent's input:

  ```text
  ORCHESTRAIL_DISPATCH_V1 {"agent_id":"worker-a","checkpoint_id":"checkpoint-a","run_id":"a1b2c3d4","schema_version":1,"session_id":"session-a"}
  ```

- The agent's final report contains exactly one unindented, compact, key-sorted JSON line
  outside code fences, no larger than 4 KiB:

  ```text
  ORCHESTRAIL_REPORT_V1 {"agent_id":"worker-a","checkpoint_id":"checkpoint-a","outcome":"ok","run_id":"a1b2c3d4","schema_version":1,"session_id":"session-a","tests":"red"}
  ```

  The required fields are `schema_version`, `run_id`, `session_id`, `agent_id`,
  `checkpoint_id`, and canonical `outcome`. Optional `tests` and `gate` use the existing
  run-log vocabularies. Unknown or duplicate keys, a noncanonical JSON encoding, more
  than one marker, or a tuple that differs from the dispatch record rejects this
  delivery and leaves its pending checkpoint unchanged. The marker cannot provide a
  step name or measured timestamp.
- Fence eligibility uses the bounded top-level lexical rules from
  [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/): an opener has at least
  three matching backticks or tildes and zero to three ASCII leading spaces; backtick
  info strings cannot contain backticks. A closer uses the same character, at least
  the opener's length, and only spaces/tabs afterward. Shorter, mixed or suffixed runs
  leave the fence open. A leading tab cannot open or close a top-level fence. Normalize
  LF, CRLF and lone-CR line delimiters without trimming marker/JSON content. Container
  prefixes are not stripped globally; a column-zero marker after a quoted/list fence
  can legitimately be outside that container. No Markdown rendering dependency is
  required. Fenced examples plus one genuine outside marker remain valid.
- Marker outcomes are direct canonical values: `ok`, `blocked`, `failed`, `skipped`, or
  `deferred`. A successful RED checkpoint uses `outcome:"ok", tests:"red"`; a GREEN
  implementation uses `outcome:"ok", tests:"green"`; validation PASS uses
  `outcome:"ok", gate:"pass"`; validation NEEDS WORK uses
  `outcome:"failed", gate:"needs-work"`; failure to establish RED uses
  `outcome:"failed", tests:"failed"`. No outcome is inferred from prose.
- The hook reads the report marker from `last_assistant_message`, then requires the
  matching dispatch line in the current transcript (`agent_transcript_path` for
  `SubagentStop`, `transcript_path` for `Stop`) and native `session_id` equal to the
  dispatch record. It considers invocation records only after that dispatch input;
  a dispatch outside the bounded transcript tail leaves coverage unavailable. It takes
  the step name only from exactly one native Skill invocation identity and checks it against `expected_skill`
  when supplied. Multiple eligible skills in one checkpoint are ambiguous: the hook
  omits the precise event and the workflow retains approximate prompt logging for those
  internal boundaries. Two calls to the same skill are still two invocations. It never
  assigns the whole interval to the last skill. A single
  session may use `step:"unknown"` only when the complete dispatch tuple uniquely
  identifies the active run; a subagent checkpoint with no unique Skill invocation is
  omitted.
- Transcript dispatch evidence must occur in recognized native input records, never
  quoted output or arbitrary text fields. Skill evidence uses native `tool_use`
  objects with `name:"Skill"`, an invocation `id`, and `input.skill`. Repeated
  representations of one invocation ID must agree; distinct IDs count separately.
- The event's canonical registered project root must equal the dispatch record's
  project. Its event kind must match the recorded boundary: `Stop` means `session`,
  and `SubagentStop` means `subagent`. A mismatch leaves ownership unchanged.
- Dispatch time and completion time come from executable clocks. Before forwarding, the
  adapter freezes the first validated completion's end timestamp and complete normalized
  producer payload under the checkpoint lock, then enters `delivering`. Every retry
  reuses that payload without rescanning a transcript that may rotate or age out of
  the bounded tail. Retry still requires matching native session, selected project,
  boundary and the native subagent ID bound at first validation, plus identical
  canonical report outcome/tests/gate. Conflicting reports never forward or mutate.
  The checkpoint becomes `accepted` only after matching the producer
  receipt. `status --checkpoint` reads private correlation state only.
- `fallback --checkpoint` may claim a still-pending checkpoint under the same lock and
  attempt one ordinary step with `note:"approximate"`. It records route ownership as
  `fallback`, then reports `fallback-attempted` regardless of the legacy helper's exit
  status: the ordinary producer offers no persistence acknowledgment. Late hooks cannot
  append after that claim. Once correlated delivery has been attempted, retry only the
  frozen payload to resolve acceptance; never switch to a legacy fallback. Process death
  or lost receipts can leave persistence uncertain, which is reported without inventing
  acceptance or attempting a second route.

### Claude hook profile and project activation

- The supported native profile is `claude-stop-v1`, reviewed on 2026-10-25 against
  Claude Code 2.1.309. The `Stop` input requires string `hook_event_name`, `session_id`,
  `cwd`, `transcript_path`, and `last_assistant_message`. `SubagentStop` additionally
  requires string `agent_id` and `agent_transcript_path`. The adapter uses the final
  response field for the report marker because the transcript may not yet contain that
  response. A missing or mistyped required field leaves the checkpoint uncovered.
- Hook stdin is limited to 1 MiB, a report marker to 4 KiB, and the transcript tail to
  16 MiB. The command hook timeout is 10 seconds. Malformed, missing, or oversized input
  emits one reason-coded coverage warning, exits zero, and makes no event mutation. The
  installed command handlers set `onFailure:"continue"` and return no blocking decision.
  Official event and environment contracts: [Claude Code hooks](https://code.claude.com/docs/en/hooks#subagentstop),
  [Claude Code Stop](https://code.claude.com/docs/en/hooks#stop), and
  [Claude Code session environment](https://code.claude.com/docs/en/env-vars).
- The installer merges handlers from `harness/claude/hooks.json` into the user settings
  file `~/.claude/settings.json`. It records exact owned handler objects and their
  enclosing selectors in `~/.config/orchestrail/hooks-installed.json`. An identical
  handler that existed before installation is not claimed. Upgrade or uninstall removes
  only exact entries recorded as owned; changed or additional user entries remain. Both
  settings and ownership records are validated before replacement and written through
  same-directory temporary files. Invalid settings or ownership data leaves originals
  unchanged and reports hook installation unavailable.
- Ownership is a multiset keyed by event, exact selector object (all enclosing-group
  keys except `hooks`) and exact handler object. Record only inserted occurrence
  counts; remove at most that count across all matching groups combined in settings
  order. Object equality ignores key order but preserves array order and omitted
  fields. A handler moved to another event/selector is unowned there and survives.
  Preserve equal unowned multiplicity rather than claiming provenance for identical
  copies. Record created-group counts separately: remove only that many matching groups
  made empty by owned-handler removal in this operation. Never remove preexisting
  groups, already-empty groups or groups retaining user handlers.
- Uninstall may retain introduced empty `hooks` or Stop/SubagentStop array containers;
  their original absence is not part of handler/group ownership. Preserve preexisting
  empty containers and all user values. Remove owned handlers and created selector
  groups by quota rather than deleting unowned structural keys.
- Settings and ownership replacements use a prepared transaction in the ownership
  sidecar under the installer lock. It contains previous/next ownership plus exact
  before/after settings digests and presence flags, without saving unrelated settings
  content. Prepare both replacements, persist the transaction, recheck the before-image,
  replace settings, then commit next ownership. On a later invocation, settings matching
  the before-image restore previous ownership; settings matching the after-image finalize
  next ownership. Recompute the requested operation afterward. If neither image matches,
  preserve settings and the prepared receipt and report unavailable coverage. Recover
  from the saved transaction even when source paths changed. Never overwrite external
  edits during recovery or claim power-loss durable atomicity across both files.
- Installer CLI: `bash scripts/install-hooks.sh install [--from <source-tree>]`
  (also `--from=<source-tree>`) or `bash scripts/install-hooks.sh uninstall`, with
  `-h/--help`. Install source precedence is explicit override, nonempty
  `ORCHESTRAIL_HOME`, then the script-parent checkout; relative overrides resolve from
  the caller's directory and are canonicalized. Uninstall depends only on the saved
  receipt/transaction and works after the old source disappears. One small JSON result
  reports `status:"installed"`, `"uninstalled"`, or `"unavailable"`. Recoverable
  installation failures warn safely without aborting other sync deployment; invalid
  CLI arguments can fail before mutation.
- Installer JSON ownership and recovery use Python 3.11 or newer's standard library behind the
  Bash entrypoint. Preserve arbitrary original settings number lexemes while comparing
  numeric JSON values mathematically for exact object equality; never round settings
  through binary floats. This explicit installer-only dependency avoids numeric-tag
  transport and a second exact comparator in jq. Missing Python makes either operation
  unavailable without settings/ownership mutation. Install additionally requires native
  jq/flock dependencies; uninstall and saved-transaction recovery do not require those
  executables or the old adapter source. Python supplies the installer lock. Hooks and
  ordinary producer writes do not acquire a Python dependency.
  The Bash entrypoint probes interpreter support before loading the engine; an older
  or unusable interpreter reports unavailable with reason `unsupported-python`
  without changing settings or ownership. Missing Python retains the existing
  missing-dependency result. This minimum follows the repository Python standard.
- Ownership sidecar version 1 has a committed form
  `{schema_version:1,state:"committed",owned:[{event,selector,handler,count}],created_groups:[{event,selector,count}]}`.
  Its prepared form is
  `{schema_version:1,state:"prepared",previous:<committed-or-null>,next:<committed-or-null>,before:{present,sha256},after:{present,sha256}}`.
  Null previous/next means an absent receipt; prepared states never nest. Presence
  true requires a 64-character lowercase hexadecimal digest; false requires null.
  Schema version and positive bounded counts use canonical integer tokens. Ownership
  keys and created-group keys are unique within their respective arrays; reject
  duplicate claims rather than multiplying deletion quotas. If a user reduced matching
  occurrences, remove at most the saved quota still present and retire stale claims.
- The portable native manifest contains only Stop/SubagentStop groups. Handlers use
  `type:"command"`, `command:"bash"`,
  `args:["@ORCHESTRAIL_HOME@/hooks/log-step-hook.sh"]`, `timeout:10`, and
  `onFailure:"continue"`. Replace only that exact permitted placeholder with the
  canonical absolute hook path, never using shell evaluation. Ownership stays out of
  native settings.
  Official [command-handler fields](https://code.claude.com/docs/en/hooks#command-hook-fields)
  and [exec-form behavior](https://code.claude.com/docs/en/hooks#exec-form-and-shell-form)
  support this argument-vector form. Anthropic's changelog introduced `args` in
  [2.1.139](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#21139)
  and `onFailure` in
  [2.1.295](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#21295),
  before the selected 2.1.309 profile. `onFailure` is accepted but
  [has no effect on Stop/SubagentStop](https://code.claude.com/docs/en/hooks#block-the-action-when-a-hook-fails);
  nonblocking behavior depends on the adapter's exit-zero/output contract and native
  event semantics. Do not infer support for unknown or older runtime profiles, or
  mistake isolated fixtures for live event-firing verification.
- Capability declarations are `harness/claude/capabilities.md` and
  `harness/codex/capabilities.md`. Claude records the verified profile and isolated
  fixture evidence; Codex states that this release installs no native adapter there
  and uses approximate logging. These describe this implementation, not permanent
  platform limitations. Unknown capability is unavailable. Sync rebuilds the existing
  global Claude/Codex instructions from their existing source bodies, then appends the
  appropriate capability block once and the current installation result separately.
  Mechanism support, installation status and accepted checkpoint coverage stay distinct.
- Registered project roots are canonical absolute paths, one per line in
  `${XDG_CONFIG_HOME:-$HOME/.config}/orchestrail/projects`. Configuration paths under
  `~/.config` in this specification use that XDG override when set.
  `scripts/setup-new-project.sh` registers its current
  project idempotently. The adapter checks the event `cwd` against registered roots on
  path-component boundaries before reading transcripts or correlation files. Paths with
  spaces are supported. Unregistered projects exit immediately with no run-log access.
- Dispatch and event handling both select the most-specific canonical registered
  ancestor of `cwd`, ignoring registry order and duplicate canonical roots. A newly
  registered nested root takes precedence; do not fall back to a broader recorded root
  when the selected root differs from dispatch metadata.
- Project setup is the sole registry writer: serialize an idempotent physical-root
  registration under a dedicated lock and use a same-directory atomic replacement.
  Validate the line-based format and preserve existing entries. Unsupported newline
  paths report registration unavailable. Installer/sync do not implicitly register
  the source checkout or prune consumer roots; the adapter reads the registry only.
- `hooks: yes` means the native event mechanism is available; it does not assert that a
  particular workflow boundary is covered. Coverage requires the matching dispatch line,
  report marker, unique skill invocation, and producer receipt. When any of those is
  missing before correlated delivery starts, the workflow keeps prompt logging with
  `note:"approximate"`. After entering `delivering`, unresolved acceptance retries only
  the frozen payload and discloses uncertain coverage; it cannot take a second route.
  `hooks: no` and
  unknown capability use that prompt-driven approximate path for every step. Run start
  and run end remain prompt-driven. A Stop event after run end is omitted and never
  reopens a run.
- Workflow routing distinguishes a boundary for which no envelope was ever issued
  from a known checkpoint. Only the former may write directly through the ordinary
  producer with `note:"approximate"`. Lost resume knowledge is not proof that no
  envelope existed; omit and disclose uncertainty instead of guessing.
- After issuing an envelope, never write that boundary directly through the ordinary
  producer. A matching accepted receipt suppresses the corresponding prompt event;
  pending status uses serialized fallback once. Missing, malformed or wrong-tuple
  status may invoke only the retained checkpoint's serialized fallback; if private
  validation cannot safely claim pending ownership, omit and disclose uncertainty.
  Delivering status keeps the correlated route, while fallback/fallback-attempted
  allows no second attempt. Controllers never fabricate native input for retries or
  infer persistence from exit zero or fallback output.
- Without restructuring current batches, `spec-run`'s existing RED return is a
  candidate for named coverage when it actually contains exactly one `pae-tests`
  invocation and matching dispatch/report/receipt. A test-level-none path has no RED
  return and no RED coverage. GREEN combines `pae-implement` and `pae-finalize`;
  validation combines three skills. Those aggregates, internal skills, synthetic
  subtask summaries, discovery/root work and arbitration retain approximate logging.
  Session-unknown coverage never becomes named-step coverage.
- Before the existing `spec-run` implementer spawn, usable native capability,
  installation and session identity may provisionally dispatch the expected
  `pae-tests` checkpoint. Retain the returned tuple and insert its original envelope
  line unchanged in the native user input. Keep the same worker, existing RED pause,
  git checkpoint and GREEN continuation. At an actual RED return, the worker appends
  one canonical report marker to its final response (`outcome:"ok",tests:"red"`);
  a genuine unique native Skill invocation remains required evidence. Resolve that
  checkpoint through status/serialized fallback before the git handoff. The named
  RED row is distinct from the approximate synthetic subtask aggregate.
- The test classifier runs inside the worker, so provisional dispatch does not prove
  a RED return will exist. A test-level-none path emits no RED report, claims no RED
  timing row and leaves the provisional checkpoint uncovered. GREEN batches must not
  reuse the RED marker. Missing actual Skill evidence, extra invocations or a wrapper
  invocation cannot become precise coverage merely because expected-skill was supplied.

### Timing definitions

- Spans are half-open integer millisecond intervals `[start_ms,end_ms)`. A span must be
  fully within its run's valid `[run_start.ts_ms,run_end.ts_ms)` interval to contribute
  timing metrics; invalid or out-of-run spans are excluded and disclosed.
- `wall_ms = run_end.ts_ms - run_start.ts_ms`. `inclusive_work_span_ms` is the sum of
  individual work spans. `work_union_ms` is the measure of their inclusive interval union. `observed_union_ms`
  is the union of valid work and explicit waiting spans. `coverage_ratio` is
  `observed_union_ms / wall_ms`; active work coverage uses the union of exclusive work
  segments divided by `wall_ms`.
- Uncovered gaps are the complement of `observed_union_ms` within the run interval.
  Waiting is reported from explicit `span_kind:"waiting"` events only and never inferred
  from gaps. Work means elapsed active span, not CPU time.
- Inclusive span duration is `end_ms - start_ms`. Exclusive segments subtract the union
  of all direct child intervals, including waiting, after validating same-run/session
  parent references, containment, and acyclicity. Each remainder retains its own
  `span_kind`. Missing or invalid relationship components are disclosed and excluded
  from exclusive calculations; valid multiple roots form a forest. Worker duration is
  the sum of exclusive work spans grouped by `(session_id,agent_id)`;
  totals across agents may exceed wall time.
- `excess_work_span_ms` is summed inclusive work-span duration minus work-union duration;
  it counts overlap with multiplicity. Wall overlap is the measure of time covered by
  at least two raw spans, including nesting. Parallel worker overlap is the measure of
  time with exclusive work from at least two distinct `(session_id,agent_id)` actors. Neither total span duration
  nor worker duration is presented as run wall time or CPU work.
- A fully covered sequential fixture has no overlaps and differs from run wall time by
  at most five percent; any remaining gaps are listed. Approximate legacy/prompt events
  remain labelled approximate and do not acquire synthetic millisecond intervals.
- Valid `step:"unknown"` session intervals contribute to observed run coverage but are
  excluded from named workflow-step timing summaries.
- Checkpoints are unique by `(run_id,session_id,checkpoint_id)`, including across
  actors. Collapse identical normalized observations once and disclose their count;
  omitted `span_kind` normalizes to `work`. Conflicting observations exclude the
  entire checkpoint key. Resolve the complete graph before arithmetic; arrival order
  and sequence numbers never establish ancestry or interval chronology.
- Repeated-checkpoint equality compares normalized producer delivery fields: actor,
  step/result, explicit interval/source/boundary/parent/kind, and every present
  caller-supplied result, context and count field from the producer contract. Presence
  and string values remain exact; historical integral number forms normalize exactly.
  Generated sequence and timestamp variations are disclosed but do not duplicate the
  span. Pipeline/project/task/flow must agree with usable run metadata; conflicting
  attribution excludes that checkpoint. Differing generated `duration_s` or unknown
  extension fields also exclude the key with a disclosed envelope conflict.
- Invalid intervals contribute no interval metrics. Otherwise valid intervals with
  invalid hierarchy relationships still contribute disclosed inclusive/union coverage,
  while their connected parent component is excluded from exclusive/worker metrics.
  Disconnected valid roots remain eligible, with partial graph coverage disclosed.
- Resolve dependency components before discarding unusable checkpoint keys. Retain
  missing, invalid or conflicting keys as non-measuring tombstones; for conflicting
  observations retain every safely established parent declaration, never select a
  winning copy. Any invalid endpoint, missing/conflicting parent, failed containment
  or cycle excludes its entire transitive parent component from exclusive, worker,
  active-exclusive and parallel calculations. A valid parent cannot silently treat
  an invalid child as absent, nor may a child of an excluded key become a root.
  Individually eligible intervals still contribute raw inclusive and union metrics.
- A lint-rejected correlated row may supply independently checked identity/parent
  fields only as negative dependency evidence, never as a timing observation or
  positive metric group. This narrow exclusion-evidence exception prevents a rejected
  child from inflating its parent's exclusive work. Unparseable rows or unusable
  correlated identities make the file's exclusive graph coverage unverified and its
  exclusive/worker/active-exclusive/parallel metrics null. Parseable rejected legacy
  rows without correlation fields do not hide graph edges. Complete lint coverage
  and graph coverage are distinct; raw eligible interval metrics may remain available.
- Containment uses endpoint inequalities, including zero-length children at a
  parent's end. A zero-length parent contains only zero-length children at that same
  instant. Zero-length spans at run end are valid and measure zero; self-parenting
  and cycles remain invalid regardless of length.
- Successive checkpoints on one actor remain separate intervals, preserving gaps.
  Overlapping exclusive intervals from distinct checkpoints on the same
  `(session_id,agent_id)` make that actor's worker total unavailable; disclose the
  overlap and retain interval coverage and other actors' valid totals.
- Same-actor overlap retains graph-valid exclusive segment unions for active-work
  coverage and distinct-actor parallel overlap. Union each actor's intervals before
  counting concurrent actors; one actor counts at most once at any instant. Disclose
  its unavailable additive total separately.
- Report inclusive waiting-span sum and waiting union separately. Waiting and active
  work can overlap across actors; they are not complements and cannot be summed into
  wall time. Precise run ratios require one unambiguous valid start/end pair;
  conflicting boundaries invalidate the denominator. A zero wall duration gives an
  unavailable ratio. Zero-length spans remain valid.
- The offline timing helper is a Bash wrapper using Python 3.11 or newer's standard library;
  producer writes, hooks and ordinary logging retain their existing dependencies.
  Keep the substantial snapshot, lint, interval and graph engine in source-only
  `scripts/run-log-timing.py` beside the small Bash entrypoint. The wrapper handles
  launch/dependency failure; Python owns argument parsing and analysis. No package
  installation or user-home script deployment is required.
  Probe the minimum interpreter version before engine startup; unsupported Python
  produces structured unavailable/null metrics just like missing dependencies.
  It reads explicitly selected snapshots without mutation, parses historical integral
  JSON forms exactly with `decimal.Decimal`, and rejects booleans, non-finite values
  and out-of-bound endpoints before integer conversion. Arithmetic uses Python
  integers throughout, including aggregate totals and the five-percent comparison.
- Timing output documents duration totals as decimal strings and ratios as exact
  numerator/denominator values; rounded display percentages identify their rounding.
  Consumers never send large totals through jq arithmetic. Missing Python emits
  structured `status:"unavailable"` with a safe reason and null metrics, exits zero,
  and leaves other retrospective analysis usable. It cannot look like an empty
  successfully examined corpus or replace unavailable metrics with measured zeros.
- Timing eligibility reuses this checkout's existing producer linter. Copy only the
  explicitly supplied files, byte for byte, into a private temporary `runs/` snapshot
  with collision-free filenames mapped to original paths; never mutate source files.
  Run `log-step.sh lint --all` against that temporary root and give Python the same
  unchanged bytes plus physical-line exclusions. Any lint violation excludes the
  entire line, including invalid outcome, tests, gate, flow, sequence or count fields.
  Do not maintain another vocabulary or pass jq-reserialized rows to Python.
- Require one verified complete `status:"ok"` lint summary and consistent file,
  line and violation counts. Partial, missing or malformed lint coverage makes all
  selected timing metrics unavailable, while disclosing known violations. jq is
  therefore an offline eligibility dependency alongside Python; missing either
  dependency cannot produce clean-looking empty metrics. Temporary snapshots are
  private and cleaned up after analysis.
- Timing CLI: `bash scripts/run-log-timing.sh [--] FILE...`, with `-h/--help`.
  Inputs are explicit paths only; no implicit store discovery, stdin corpus or active
  metadata reads. Deduplicate repeated canonical paths in caller order. Each input file
  describes one run; inconsistent run identities within a file or distinct selected
  files claiming the same run identity are ambiguous and unavailable for that run.
  Missing inputs, invalid arguments and failed reads produce structured unavailable
  results, never successful empty-corpus metrics.
- Output is one version-1 JSON object with `status`, `coverage`, `runs` and
  `diagnostics`. Coverage reports lint status, selected files, examined lines, invalid
  lines, violation count and whether the invalid-line count is exact. Unavailable
  corpus metrics and runs are null. A run reports its file, identity, status, metrics,
  spans, workers, named-step summaries and reason-coded diagnostics; never emit raw
  records, notes or conversation context. Millisecond endpoints and totals are decimal
  strings; ratios use exact `numerator_ms` and `denominator_ms` strings, or null when
  unavailable. Gaps use explicit endpoint pairs. Known exclusions produce partial
  results; unverified lint makes all timing unavailable. Gaps alone do not imply an
  invalid corpus or waiting.
- Lint completeness checks count physical input lines by LF bytes only (empty files
  have zero lines, a nonempty unterminated final line counts once). Require exactly
  one final summary, no unknown diagnostic kinds, nonnegative integer nonboolean
  controls, and exact file/line/violation/unique-invalid-line counts. Every violation
  references a known snapshot file and an in-range physical line with nonempty field
  and code. Verify unchanged snapshot inventory and bytes around lint; malformed or
  incomplete diagnostics make coverage unavailable and known violations lower bounds.
