# docs/ — documents about Orchestrail

Everything here is *about* the system; the system itself is `workflows/`, `rules/`,
`principles/`, `templates/`, and `scripts/`. Placement rule:
`.ai/principles/coding.md → Document placement`.

## Manuals
- [USAGE.md](USAGE.md) — operating manual: setup, project initialisation, daily workflow, command reference, status formats, hook coverage and exact retrospective timing
- [Repository scripts](../scripts/README.md#exact-run-timing) — explicit-file timing invocation, dependencies and output semantics
- [SPEC-RUN-QUICKSTART.md](SPEC-RUN-QUICKSTART.md) — operating procedure for `/spec-run`
- [MODEL-CATALOG.md](MODEL-CATALOG.md) — optional cached selection, explicit refresh/rollback, provider-column compatibility and offline helper examples

## Audits (`audits/`)

- [Specification delivery review](audits/2026-11-06-specification-delivery-review.md) — all 23 specifications, delivered foundations, outstanding scope, owner-directed runtime closure, and verification limits
- [Usage telemetry review](audits/2026-10-30-usage-telemetry-review.md) — isolated per-PR reviews, behavioral repairs, independent rechecks and integration evidence
- Historical workflow clarity and size audit (`2026-10-28-workflow-clarity-and-size.md`) — unavailable in the current tree; do not use it as evidence of delivery
- [2026-10-26-hook-logging-final-review.md](audits/2026-10-26-hook-logging-final-review.md) — independent per-PR reviews, producer repairs, complete validation and verified integration
- [AUDIT-PROMPT.md](audits/AUDIT-PROMPT.md) — prompt for an independent audit of `/spec-run`
- [2026-07-21-logic-audit-fixes.md](audits/2026-07-21-logic-audit-fixes.md) — the 20-finding logic audit and its fix spec

## Analysis (`analysis/`)

- [Validator runtime specification review](analysis/2026-11-05-validator-runtime-review.md) — current test architecture, measured git-rails cost, corrected runtime requirements and independent validation cycles
- Historical usage telemetry specification review (`2026-10-27-usage-telemetry-spec-review.md`) — unavailable in the current tree; use the delivered [telemetry review](audits/2026-10-30-usage-telemetry-review.md) for available implementation evidence
- [2026-09-16-comparative-analysis.ru.md](analysis/2026-09-16-comparative-analysis.ru.md) — full analysis vs BMAD, Spec Kit, Kiro, OpenSpec, Superpowers, Agent OS, Conductor; pros/cons; fit; improvements (English translation of the historical Russian record)
- [2026-09-16-rules-workflows-naming-review.md](analysis/2026-09-16-rules-workflows-naming-review.md) — why five rule/workflow names collide, what differs, and renaming recommendations
- [2026-09-16-comparative-analysis-tldr.ru.md](analysis/2026-09-16-comparative-analysis-tldr.ru.md) — TL;DR of the above (English translation of the historical Russian record)

## Roadmap
Actionable improvements are specs, not documents: see [`.ai/specs/README.md`](../.ai/specs/README.md).
