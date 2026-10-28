# docs/ — documents about Orchestrail

Everything here is *about* the system; the system itself is `workflows/`, `rules/`,
`principles/`, `templates/`, and `scripts/`. Placement rule:
`.ai/principles/coding.md → Document placement`.

## Manuals
- [USAGE.md](USAGE.md) — operating manual: setup, project initialisation, daily workflow, command reference, status formats, hook coverage and exact retrospective timing
- [Repository scripts](../scripts/README.md#exact-run-timing) — explicit-file timing invocation, dependencies and output semantics
- [SPEC-RUN-QUICKSTART.md](SPEC-RUN-QUICKSTART.md) — operating procedure for `/spec-run`

## Audits (`audits/`)

- [Workflow clarity and size audit](audits/2026-10-28-workflow-clarity-and-size.md) — all workflow files, corrected execution contracts, source-size comparison and specification reconciliation
- [2026-10-26-hook-logging-final-review.md](audits/2026-10-26-hook-logging-final-review.md) — independent per-PR reviews, producer repairs, complete validation and verified integration
- [AUDIT-PROMPT.md](audits/AUDIT-PROMPT.md) — prompt for an independent audit of `/spec-run`
- [2026-07-21-logic-audit-fixes.md](audits/2026-07-21-logic-audit-fixes.md) — the 20-finding logic audit and its fix spec

## Analysis (`analysis/`)

- [Usage telemetry specification review](analysis/2026-10-27-usage-telemetry-spec-review.md) — request finality, exact cost accounting, coverage, immutable usage records and advisory monitoring
- [2026-09-16-comparative-analysis.ru.md](analysis/2026-09-16-comparative-analysis.ru.md) — full analysis vs BMAD, Spec Kit, Kiro, OpenSpec, Superpowers, Agent OS, Conductor; pros/cons; fit; improvements (Russian)
- [2026-09-16-rules-workflows-naming-review.md](analysis/2026-09-16-rules-workflows-naming-review.md) — why five rule/workflow names collide, what differs, and renaming recommendations
- [2026-09-16-comparative-analysis-tldr.ru.md](analysis/2026-09-16-comparative-analysis-tldr.ru.md) — TL;DR of the above (Russian)

## Roadmap
Actionable improvements are specs, not documents: see [`.ai/specs/README.md`](../.ai/specs/README.md).
