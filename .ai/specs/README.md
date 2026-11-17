# Specifications and execution roadmap

Review date: 2026-11-06. This index separates delivered source cleanup from planned
roadmap work. The owner authorized workflow optimization and specification reconciliation;
that request does not schedule unrelated roadmap implementation, deployment or paid
comparisons. Project artifacts use English.

Start with `/phase-discovery .ai/specs/<file>.md`; use `/discovery` after the command
migration. Completed records are historical evidence, not work to repeat. A completed
task does not authorize merging, tagging, or publication.

## Current implementation status

The [delivery review](../../docs/audits/2026-11-06-specification-delivery-review.md)
covers all **23 specifications** at main revision `23bded3`: seven historically
completed foundations (00-06), one partially delivered runtime specification whose
task was closed by owner decision, and fifteen planned/backlog specifications.
Each specification now distinguishes existing foundations from its outstanding scope.
The review does not certify a fresh full suite or deployed installations.

Runtime task closure is administrative. Warning-fixture, identity-scan and source-guard
changes are integrated; concurrent acceptance execution, opt-in timing, an additional
identity-output I/O correction and comparative performance acceptance remain undelivered.
Deleted experimental branch names do not count as delivery. The dated review above remains
historical evidence. The state tool was merged and archived on 2026-11-16, as recorded in
[progress](../memory/progress.md). Current active work is listed in
[task state](../memory/state.md); the rules/workflows audit remains separately scheduled
and the post-merge closure implementation below does not advance other roadmap scope.

## Owner-scheduled post-merge closure

On 2026-11-17 the owner approved [task finalization](24-task-finalization.md) as a separate development task, outside the earlier roadmap ordering. Implementation was independently validated locally on 2026-11-18 on the pinned multi-repository support dependency: full validator 725/0/2 and all 156 finalization acceptance tests passed; staged provider outputs were generated in isolation. Integration, live synchronization and this task's own finalization remain owner-controlled follow-ups. It does not advance unrelated roadmap scope or authorize deployment. Current execution evidence lives in [task state](../tasks/todo/task-24-task-finalization/state.md).

## Nine token optimization workstreams

There are **nine feature-sized tasks: two expanded existing specs and seven new specs**.
Supporting roadmap items remain separate. Each workstream has one owning spec;
consumers reference its contract rather than redefining it.

| # | Workstream | Owning spec | Boundary and evidence |
|---|---|---|---|
| 1 | Telemetry and baseline | [05 — telemetry](completed/05-cost-and-duration-telemetry.md) | Actual usage, role/stage/attempt attribution, cache accounting, API-equivalent valuation, coverage and accepted-result cost |
| 2 | Compact context preparation | [12 — task context](12-task-context-and-reuse.md) | Stable context reuse, fresh leaf views, task contracts, relevant files, load-once behavior, cache-compatible ordering |
| 3 | Shorter instructions and outputs | [11 — context tiering](11-context-tiering.md) | Compact rules, on-demand reference, explicit loads, concise reports with evidence |
| 4 | Orchestrator overhead | [13 — controller overhead](13-orchestrator-overhead.md) | Fewer status turns, bounded history, deterministic inspection and delta rendering; shared state stays single-writer |
| 5 | Review overhead | [15 — scoped verification](15-scoped-verification.md) | Independent review, evidence reuse for unchanged inputs, finding-led repair review with impact expansion |
| 6 | Bounded tool output | [14 — tool output](14-bounded-tool-output.md) | Bounded previews, full local artifacts, preserved errors and exit status, complete retrieval |
| 7 | Reasoning effort | [16 — effort policy](16-reasoning-effort-policy.md) | Role/stage/complexity-based effort, capability checks, conservative fallback, measured quality |
| 8 | Local repair and escalation | [17 — repair policy](17-local-repair-and-escalation.md) | Opt-in bounded repair, preserved correct code and RED evidence, independent recheck, explicit escalation |
| 9 | Economical decomposition | [18 — decomposition](18-cost-aware-decomposition.md) | Coherent leaves, measured setup/review overhead, architectural boundaries, integration and AC coverage |

This is an ownership map, not a measured ranking of savings. No percentage or dollar
saving is established here. Word/byte reductions are diagnostics; token usage and
API-equivalent valuation are separate measurements.

## Delivered source cleanup — 2026-10-28

The workflow set now has clearer guards, resumable phase/checkpoint handling, explicit
parent-versus-standalone context loading, consistent model-selection scoring, protected
compression, conservative restack recovery, and source-backed spec reconciliation.
A separate token-efficiency pass removed repeated prose; instruction-contract checks
cover these interfaces. The historically cited `docs/audits/2026-10-28-workflow-clarity-and-size.md`
is absent from the current tree and is not available evidence. These are source changes, not evidence of measured token/cost
savings or deployed behavior.

That cleanup alone partially advanced 04/11/08/12/13/15 without completing them.
Cached catalog selection, conservative quality/economic filtering, compatible plan
resolution and installed workflow guidance were subsequently delivered under
[04](completed/04-model-catalog-cache.md), with 594 required checks passing and 87 focused model tests.
Full rule inventory/naming, reference tiers/load metadata, content-hash packets,
effort/repair policies and economic evaluation remain separate work. Completed 00–06
remain foundations, not work to repeat. No deployment or model-usage savings is claimed.

## Shared acceptance gates

These gates are part of each owning spec's acceptance contract. Feature implementation
can be accepted with deterministic evidence. Promotion of a cheaper default also needs
an explicitly approved comparative evaluation under spec 10.

| Gate | Required evidence |
|---|---|
| G1 — Attribution | Source/deployed versions, actual harness/model, configuration, role/stage/attempt, usage coverage, and experiment identity where applicable. Use spec 05's schema; missing counters are not zero. |
| G2 — Comparable measurement | Same initial revision, specification, acceptance criteria and task set. Report input, cached input, cache writes, output/reasoning where available, API-equivalent cost, calls, retries, wall time and coverage separately. No model-run claims from word counts or simulations. |
| G3 — Independent quality | Preserve test-first order, frozen RED evidence, contracts, git rails, owner stops, independent Validator and integration checks. Tests and reviewer verdicts are evidence, neither is absolute truth. Evaluate held-out criteria and later defects under spec 10. |
| G4 — Compatibility | Legacy artifacts remain readable. Missing optional capabilities use a documented conservative path; unsafe or ambiguous state stops before mutation. Unknown usage stays unknown. No hidden model substitution. |
| G5 — Ownership | Only the authorized writer updates shared state and git. Helpers do not spawn models, become a mandatory runtime, or bypass approval/sandbox policies. Spec 07 is scheduled as an optional, unwired tool (ADR-0021). |
| G6 — Testing | New behavior has failing deterministic fixtures before implementation and passing fixtures afterward. Markdown receives contract/reachability checks. Paid runs never start during ordinary validation, sync, or default CI jobs. |
| G7 — Rollback | Document disable/resume from the last verified checkpoint using the previous policy. Preserve task history, evidence and verified code. |
| G8 — Economics | Compare expected total cost of a correct result, including planning, tools, verification, repair and escalation. Subscription payments are actual billing; API-equivalent USD is not an invoice or quota estimate. No production cost/time cap is introduced. |

## Dependency order

Historical foundations follow ADR-0009 and completed work. The requested optimization
program adds the edges below; rows are one valid sequential order. Record changes to
accepted behavioral contracts in an ADR during implementation. This index does not
rewrite historical decisions. Files in `scripts/` are the current helpers; old bare
script names in historical context identify their earlier locations.

| Order | Spec | Prerequisites | Review disposition |
|---|---|---|---|
| Done | [00 — scrub](completed/00-sensitive-data-scrub.md) | — | Retain completed history and approved exceptions |
| Done | [01 — source of truth](completed/01-git-source-of-truth.md) | 00 | Retain license/tag deferrals; unchecked historical boxes do not reopen the task |
| Done | [02 — log vocabulary](completed/02-run-log-vocabulary-validation.md) | 01 | Retain strict grammar, non-blocking writes and read-only lint; merge status belongs to task records |
| 1 | [08 — audit](08-rules-workflows-audit.md) | 01 | Refresh actual inventory; identify duplicated loads and ownership |
| 2 | [09 — harnesses/naming](09-model-only-harnesses-and-rule-naming.md) | 01, 08 | Preserve IDs; capability-based behavior and current script paths |
| Done | [04 — catalog](completed/04-model-catalog-cache.md) | Current-invocation capabilities; wider 09 migration remains separate | Reviewed cached catalog, conservative selection and compatible plan resolution; PRs #31–#36 merged |
| Done | [03 — logging](completed/03-hook-based-logging.md) | 02; minimal harness/registry scaffold | Reviewed explicit correlation, owned hooks and exact timing; minimal hook scaffold only, wider harness migration remains pending |
| Done | [05 — telemetry](completed/05-cost-and-duration-telemetry.md) | 02, 03 | Reviewed offline telemetry and recovery; PRs #37–#63 merged; 619 required checks passed |
| Done | [06 — git rails](completed/06-harness-git-rails.md) | 05 (09 not required, ADR-0017) | Integrated before 08/09: #64 marked merged, #65–#75 closed after local stack integration; historical 717 required checks passed; residual risks X1–X20 retained |
| Closed; partial | [06-1 — validator runtime](06-1-test-suite-runtime.md) | — | Owner closed the task after #77–#79 merged. Warning-prefix, per-file scan and bounded guard delivered; scheduling, timing and comparative targets remain unmet. No automatic resumption or passing AC claim |
| 6 | [10 — regression/evaluation](10-golden-run-tests.md) | 01, 09, 05, 06 | Offline checks, paid goldens, independent quality comparisons |
| 7 | [11 — instructions/output](11-context-tiering.md) | 09, 10 | Expanded workstream 3 |
| 8 | [12 — context](12-task-context-and-reuse.md) | 05, 11, 10 | New workstream 2 |
| 9 | [13 — orchestrator](13-orchestrator-overhead.md) | 06, 10, 12 | New workstream 4; no general state engine |
| 10 | [14 — tool output](14-bounded-tool-output.md) | 06, 10, 12 | New workstream 6 |
| 11 | [15 — verification](15-scoped-verification.md) | 10, 12, 13, 14 | New workstream 5 |
| 12 | [16 — effort](16-reasoning-effort-policy.md) | 04, 05, 10, 13, 15 | New workstream 7 |
| 13 | [17 — repair/escalation](17-local-repair-and-escalation.md) | 04, 06, 10, 13, 15, 16 | New workstream 8 |
| 14 | [18 — decomposition](18-cost-aware-decomposition.md) | 04, 05, 10, 12, 13, 15 | New workstream 9 |
| 15 | [19 — references](19-generated-reference-docs.md) | 09, 11 | Render metadata without inlining optional context |
| 16 | [20 — installer and profiles](20-public-installer-and-profiles.md) | 01, 19, 09 | Split from 21 on 2026-11-16: installer, ownership records, neutral core and profiles |
| 17 | [21 — public readiness](21-open-source-readiness.md) | 01, 10, 19, 20 | Accurate docs; license/release remain explicit owner actions |
| 18 | [22 — composite branch model](22-composite-branch-model.md) | 09, 10, 02, 03, 05, 15 (12, 17 when delivered) | Split from 23 on 2026-11-16: one branch per composite, sequential children on temporary branches |
| 19 | [23 — composite children](23-composite-branch-model-and-parallel-children.md) | 22, 09, 10, 02, 03, 05, 12, 13, 15, 17, 18 | Parallel children of one composite; integrate isolation, context, review and attribution before parallel rollout |
| Delivered | [07 — state tool](completed/07-state-tool.md) | — | Scheduled by the owner on 2026-11-13 (ADR-0021); delivered 2026-11-16 on stacked pull requests #80–#98, merged into main the same day (ADR-0022); specification archived; optional and unwired, not a prerequisite of the nine tasks |

## Renumbering — 2026-11-16

The sixteen open specifications were renumbered so that the file number is the position in
the execution order (ADR-0023). Completed specifications 00–07 and 06-1 keep their numbers.
Every reference in this knowledge base and under `docs/` uses the new numbers, including
decision records, the progress log and completed task records. Commit messages, pull
request titles and branch names created before 2026-11-16 keep the old numbers; read them
through this table.

| Old number | New number | File |
|---|---|---|
| 13a | 08 | [08-rules-workflows-audit.md](08-rules-workflows-audit.md) |
| 13 | 09 | [09-model-only-harnesses-and-rule-naming.md](09-model-only-harnesses-and-rule-naming.md) |
| 09 | 10 | [10-golden-run-tests.md](10-golden-run-tests.md) |
| 08 | 11 | [11-context-tiering.md](11-context-tiering.md) |
| 14 | 12 | [12-task-context-and-reuse.md](12-task-context-and-reuse.md) |
| 15 | 13 | [13-orchestrator-overhead.md](13-orchestrator-overhead.md) |
| 17 | 14 | [14-bounded-tool-output.md](14-bounded-tool-output.md) |
| 16 | 15 | [15-scoped-verification.md](15-scoped-verification.md) |
| 18 | 16 | [16-reasoning-effort-policy.md](16-reasoning-effort-policy.md) |
| 19 | 17 | [17-local-repair-and-escalation.md](17-local-repair-and-escalation.md) |
| 20 | 18 | [18-cost-aware-decomposition.md](18-cost-aware-decomposition.md) |
| 10 | 19 | [19-generated-reference-docs.md](19-generated-reference-docs.md) |
| 11a | 20 | [20-public-installer-and-profiles.md](20-public-installer-and-profiles.md) |
| 11 | 21 | [21-open-source-readiness.md](21-open-source-readiness.md) |
| 12a | 22 | [22-composite-branch-model.md](22-composite-branch-model.md) |
| 12 | 23 | [23-composite-branch-model-and-parallel-children.md](23-composite-branch-model-and-parallel-children.md) |

Identifiers that embedded an old number were renamed with it: `AUD-13A-NNN` and
`AMD-13A-NN` are `AUD-08-NNN` and `AMD-08-NN`; `blocks_13`, `spec13_default`,
`spec13_optional`, `in_spec13_grammar` and `spec13-unavailable` use `09`;
`13a-extract-1` is `08-extract-1`; delivery stages 12A and 12B are 23A and 23B.

## Review record and remaining decisions

The 2026-11-06 reconciliation reviewed all **23 specifications**: seven completed
records retain delivery history and owner deferrals; sixteen root-level records include
the administratively closed, partially delivered runtime scope and fifteen planned/backlog
specifications. The seven optimization specs added on 2026-10-21 remain planned; this
index is not a spec. Shared acceptance gates remain binding; metadata-only context reuse,
textual review/checkpoint rules and existing offline tests do not satisfy the future
content-hash, bounded-output, effort, repair, parallel-scheduler or evaluation interfaces.

The missing historical clarity report was not reconstructed. Broken current local links
were repaired to available canonical records. Historical pinned source links and all
requirement/acceptance identifiers were retained.

The nine workstreams cover the identified mechanisms. Cheap-first execution is still a
hypothesis. Spec 10 compares strong-first, cheap execution plus strong verification,
strong planning plus cheap execution, adaptive chains, tiered verification, and hybrids.
Strong-first remains valid where expected repair cost is higher.

Before paid comparison, the owner chooses the task set, quality tolerances, available
models, sample/repetition counts, experimental spend/time limits and stop conditions.
These limits do not become production run budgets. Unanswered experimental settings
do not block deterministic implementation or authorize paid work.

Later separate candidates: RED-set enforcement hook, secrets/PII review gate, optional
third harnesses and a documentation site. Optimization does not waive existing RED-set
protection, test-first order or independent review.
