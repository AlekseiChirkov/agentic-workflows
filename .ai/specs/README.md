# Specifications and execution roadmap

Review date: 2026-10-28. This index separates delivered source cleanup from planned
roadmap work. The owner authorized workflow optimization and specification reconciliation;
that request does not schedule unrelated roadmap implementation, deployment or paid
comparisons. Project artifacts use English.

Start with `/phase-discovery .ai/specs/<file>.md`; use `/discovery` after the command
migration. Completed records are historical evidence, not work to repeat. A completed
task does not authorize merging, tagging, or publication.

## Nine token optimization workstreams

There are **nine feature-sized tasks: two expanded existing specs and seven new specs**.
Supporting roadmap items remain separate. Each workstream has one owning spec;
consumers reference its contract rather than redefining it.

| # | Workstream | Owning spec | Boundary and evidence |
|---|---|---|---|
| 1 | Telemetry and baseline | [05 — telemetry](05-cost-and-duration-telemetry.md) | Actual usage, role/stage/attempt attribution, cache accounting, API-equivalent valuation, coverage and accepted-result cost |
| 2 | Compact context preparation | [14 — task context](14-task-context-and-reuse.md) | Stable context reuse, fresh leaf views, task contracts, relevant files, load-once behavior, cache-compatible ordering |
| 3 | Shorter instructions and outputs | [08 — context tiering](08-context-tiering.md) | Compact rules, on-demand reference, explicit loads, concise reports with evidence |
| 4 | Orchestrator overhead | [15 — controller overhead](15-orchestrator-overhead.md) | Fewer status turns, bounded history, deterministic inspection and delta rendering; shared state stays single-writer |
| 5 | Review overhead | [16 — scoped verification](16-scoped-verification.md) | Independent review, evidence reuse for unchanged inputs, finding-led repair review with impact expansion |
| 6 | Bounded tool output | [17 — tool output](17-bounded-tool-output.md) | Bounded previews, full local artifacts, preserved errors and exit status, complete retrieval |
| 7 | Reasoning effort | [18 — effort policy](18-reasoning-effort-policy.md) | Role/stage/complexity-based effort, capability checks, conservative fallback, measured quality |
| 8 | Local repair and escalation | [19 — repair policy](19-local-repair-and-escalation.md) | Opt-in bounded repair, preserved correct code and RED evidence, independent recheck, explicit escalation |
| 9 | Economical decomposition | [20 — decomposition](20-cost-aware-decomposition.md) | Coherent leaves, measured setup/review overhead, architectural boundaries, integration and AC coverage |

This is an ownership map, not a measured ranking of savings. No percentage or dollar
saving is established here. Word/byte reductions are diagnostics; token usage and
API-equivalent valuation are separate measurements.

## Delivered source cleanup — 2026-10-28

The workflow set now has clearer guards, resumable phase/checkpoint handling, explicit
parent-versus-standalone context loading, consistent model-selection scoring, protected
compression, conservative restack recovery, and source-backed spec reconciliation.
A separate token-efficiency pass removed repeated prose; instruction-contract checks
cover these interfaces. See the [source audit](../../docs/audits/2026-10-28-workflow-clarity-and-size.md). These are source changes, not evidence of measured token/cost
savings or deployed behavior.

This partially advances the concerns of 04/08/13a/14/15/16 but completes none of those
specifications. Full rule inventory/naming, reference tiers/load metadata, content-hash
packets, catalog persistence, helper APIs, effort/repair policies and economic evaluation
remain pending. Completed 00–03 are foundations, not work to repeat.

## Shared acceptance gates

These gates are part of each owning spec's acceptance contract. Feature implementation
can be accepted with deterministic evidence. Promotion of a cheaper default also needs
an explicitly approved comparative evaluation under spec 09.

| Gate | Required evidence |
|---|---|
| G1 — Attribution | Source/deployed versions, actual harness/model, configuration, role/stage/attempt, usage coverage, and experiment identity where applicable. Use spec 05's schema; missing counters are not zero. |
| G2 — Comparable measurement | Same initial revision, specification, acceptance criteria and task set. Report input, cached input, cache writes, output/reasoning where available, API-equivalent cost, calls, retries, wall time and coverage separately. No model-run claims from word counts or simulations. |
| G3 — Independent quality | Preserve test-first order, frozen RED evidence, contracts, git rails, owner stops, independent Validator and integration checks. Tests and reviewer verdicts are evidence, neither is absolute truth. Evaluate held-out criteria and later defects under spec 09. |
| G4 — Compatibility | Legacy artifacts remain readable. Missing optional capabilities use a documented conservative path; unsafe or ambiguous state stops before mutation. Unknown usage stays unknown. No hidden model substitution. |
| G5 — Ownership | Only the authorized writer updates shared state and git. Helpers do not spawn models, become a mandatory runtime, or bypass approval/sandbox policies. Spec 07 stays backlog. |
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
| 1 | [13a — audit](13a-rules-workflows-audit.md) | 01 | Refresh actual inventory; identify duplicated loads and ownership |
| 2 | [13 — harnesses/naming](13-model-only-harnesses-and-rule-naming.md) | 01, 13a | Preserve IDs; capability-based behavior and current script paths |
| 3 | [04 — catalog](04-model-catalog-cache.md) | 13 | Availability, consistent scoring and cached catalog |
| Done | [03 — logging](completed/03-hook-based-logging.md) | 02; minimal harness/registry scaffold | Reviewed explicit correlation, owned hooks and exact timing; minimal hook scaffold only, wider harness migration remains pending |
| 4 | [05 — telemetry](05-cost-and-duration-telemetry.md) | 02, 03 | Expanded workstream 1 |
| 5 | [06 — git rails](06-harness-git-rails.md) | 13, 05 | Enforcement remains effective through helpers and repairs |
| 6 | [09 — regression/evaluation](09-golden-run-tests.md) | 01, 13, 05, 06 | Offline checks, paid goldens, independent quality comparisons |
| 7 | [08 — instructions/output](08-context-tiering.md) | 13, 09 | Expanded workstream 3 |
| 8 | [14 — context](14-task-context-and-reuse.md) | 05, 08, 09 | New workstream 2 |
| 9 | [15 — orchestrator](15-orchestrator-overhead.md) | 06, 09, 14 | New workstream 4; no general state engine |
| 10 | [17 — tool output](17-bounded-tool-output.md) | 06, 09, 14 | New workstream 6 |
| 11 | [16 — verification](16-scoped-verification.md) | 09, 14, 15, 17 | New workstream 5 |
| 12 | [18 — effort](18-reasoning-effort-policy.md) | 04, 05, 09, 15, 16 | New workstream 7 |
| 13 | [19 — repair/escalation](19-local-repair-and-escalation.md) | 04, 06, 09, 15, 16, 18 | New workstream 8 |
| 14 | [20 — decomposition](20-cost-aware-decomposition.md) | 04, 05, 09, 14, 15, 16 | New workstream 9 |
| 15 | [10 — references](10-generated-reference-docs.md) | 13, 08 | Render metadata without inlining optional context |
| 16 | [11 — public readiness](11-open-source-readiness.md) | 01, 09, 10, 13 | Accurate docs; license/release remain explicit owner actions |
| 17 | [12 — composite children](12-composite-branch-model-and-parallel-children.md) | 13, 09, 02, 03, 05, 14, 15, 16, 19, 20 | Integrate isolation, context, review and attribution before parallel rollout |
| Backlog | [07 — state tool](07-state-tool.md) | — | Remains deferred, not a prerequisite of the nine tasks |

## Review record and remaining decisions

The 2026-10-28 reconciliation reviewed all **22 specifications**: four completed
records retain delivery history, and eighteen active/backlog records reflect current
source. The seven optimization specs added on 2026-10-21 remain planned; this index is
not a spec. Completed hook logging now links to its archived source.

The nine workstreams cover the identified mechanisms. Cheap-first execution is still a
hypothesis. Spec 09 compares strong-first, cheap execution plus strong verification,
strong planning plus cheap execution, adaptive chains, tiered verification, and hybrids.
Strong-first remains valid where expected repair cost is higher.

Before paid comparison, the owner chooses the task set, quality tolerances, available
models, sample/repetition counts, experimental spend/time limits and stop conditions.
These limits do not become production run budgets. Unanswered experimental settings
do not block deterministic implementation or authorize paid work.

Later separate candidates: RED-set enforcement hook, secrets/PII review gate, optional
third harnesses and a documentation site. Optimization does not waive existing RED-set
protection, test-first order or independent review.
