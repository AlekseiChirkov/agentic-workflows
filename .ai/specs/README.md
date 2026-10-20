# specs/ — improvement roadmap for Orchestrail

One spec per change, in the shape of `templates/spec.md` (spec 13 uses the full SDD
shape of `/spec-draft`). Start a task with `/phase-discovery .ai/specs/<NN>-<slug>.md`
(`/discovery` after spec 13). Order follows ADR-0009 Decision 7 and ADR-0008: scrub what must never be
committed, make the source reviewable and self-describing, then stabilise the log contract, then
automate recording and protection, then documentation and tests, then composite
parallelism. All owner decisions behind these specs are in ADR-0009.

| Order | NN | Spec | Effort | Depends on | Why this position |
|---|---|---|---|---|---|
| 1 | 00 | [sensitive-data-scrub — completed](completed/00-sensitive-data-scrub.md) | days | — | Completed: current-content cleanup and forbidden-token guard; owner accepted existing ancestry |
| 2 | 01 | [git-source-of-truth](01-git-source-of-truth.md) | days | 00 | git, Orchestrail rename, `VERSION`, minimal public slice |
| 3 | 13a | [rules-workflows-audit](13a-rules-workflows-audit.md) | days | 01 | evidence for every rename; may amend 13 |
| 4 | 13 | [model-only-harnesses-and-rule-naming](13-model-only-harnesses-and-rule-naming.md) | weeks | 01, 13a | drop Windsurf/Devin; `harness/` + capabilities; `<kind>-<subject>` rules; command renames |
| 5 | 04 | [model-catalog-cache](04-model-catalog-cache.md) | hours | 13 | independent; removes up to 3 h per run |
| 6 | 02 | [run-log-vocabulary-validation](02-run-log-vocabulary-validation.md) | hours | 01 | stabilise the log contract |
| 7 | 03 | [hook-based-logging](03-hook-based-logging.md) | days | 02, 13 | real timestamps via hooks |
| 8 | 05 | [cost-and-duration-telemetry](05-cost-and-duration-telemetry.md) | days | 02, 03 | tokens, cost, anomaly warnings — no budgets |
| 9 | 06 | [harness-git-rails](06-harness-git-rails.md) | days | 13, 05 | forbidden git operations become impossible |
| 10 | 09 | [golden-run-tests](09-golden-run-tests.md) | weeks | 01, 13 | behavioural regression tests, release-only |
| 11 | 08 | [context-tiering](08-context-tiering.md) | weeks | 13, 09 | ≤ 700 words per always-on rule |
| 12 | 10 | [generated-reference-docs](10-generated-reference-docs.md) | days | 13, 08 | `docs/reference/`, always-on from core body |
| 13 | 11 | [open-source-readiness](11-open-source-readiness.md) | days | 01, 09, 10, 13 | installer, profiles, examples, scrubbing, `1.0.0` |
| 14 | 12 | [composite-branch-model-and-parallel-children](12-composite-branch-model-and-parallel-children.md) | weeks | 13, 09, 02, 03 | one branch + one PR per composite; parallel children |
| backlog | 07 | [state-tool](07-state-tool.md) | weeks | — | deferred by the owner; shape agreed |

Completed specifications are retained in `completed/`; their task records are in `../tasks/completed/`.

Later candidates without a spec yet: RED-set protection hook (refuse test-file edits
during GREEN without an amendment note); `/spec-run` on a second orchestrating harness;
EARS/Given-When-Then acceptance criteria with AC → test → commit traceability in PR
bodies; a secrets/PII gate in `/pv-review`; machine-readable retro output over contract
versions; a documentation site.
