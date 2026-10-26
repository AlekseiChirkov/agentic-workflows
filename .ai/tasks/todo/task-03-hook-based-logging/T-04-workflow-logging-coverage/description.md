# Coverage-aware workflow logging

## Goal
Workflow instructions wire supported dispatch/report checkpoints and preserve approximate prompt logging at every unobserved boundary.

## Context
- Dependencies: T-03.
- Constraints: preserve validated nonblocking logging, explicit attribution and private active correlation; read the parent solution design.
- Reason: one coherent coverage-aware workflow logging component with its own independently verifiable acceptance cluster.

## Scope
In scope: Workflow instructions wire supported dispatch/report checkpoints and preserve approximate prompt logging at every unobserved boundary.

Out of scope: cost/token schemas, git protection hooks, broad harness migration, historical telemetry mutation, automatic merges. Other leaves own their named components.

Target files: workflows/spec-run.md, workflows/phase-pipeline.md, workflows/phase-discovery.md, workflows/phase-execution.md, workflows/phase-validation.md, rules/orchestration.md, rules/run-log.md, tests/hook-workflow-contract.sh. Paths may be refined after inspecting existing patterns; report additions explicitly.

## Steps
1. Freeze executable or contract integration checks for covered checkpoints versus unobserved internal boundaries and hooks-unavailable behavior.
2. Define capability and demonstrated-boundary selection once in the canonical log rule, including fallback note approximate.
3. Integrate the concrete adapter dispatch envelope, exact report marker and receipt status at reliably observed orchestrated checkpoints with no model-written timestamps. Suppress a prompt event only after matching acceptance; use the adapter's serialized fallback for registered checkpoints.
4. Keep run-start and run-end prompt-driven and retain internal per-step instructions where generic Stop cannot observe completion.
5. Update every prompt-driven producer path to carry approximate notes and provide explicit fallback on unavailable payload or required capability.
6. Verify documentation/contract consistency and representative synthetic single-session and sub-agent paths.

## Acceptance Criteria
- Given hooks no or unavailable payload capability, every prompt-driven step uses note approximate and run boundaries remain prompt-driven.
- Given batched sub-agent skills, only demonstrably observed checkpoints suppress the corresponding prompt event; internal boundaries retain approximate instructions.
- Given supported dispatch and report markers, instructions supply explicit correlation and canonical outcome without inferring identity from active history or deriving skill from prose.

## Test Plan
- Level: integration, contract
- Scenarios:
  - Given hooks no or unavailable payload capability, every prompt-driven step uses note approximate and run boundaries remain prompt-driven. → assert the stated observable result in isolated executable fixtures.
  - Given batched sub-agent skills, only demonstrably observed checkpoints suppress the corresponding prompt event; internal boundaries retain approximate instructions. → assert the stated observable result in isolated executable fixtures.
  - Given supported dispatch and report markers, instructions supply explicit correlation and canonical outcome without inferring identity from active history or deriving skill from prose. → assert the stated observable result in isolated executable fixtures.
- Edge cases: empty/null inputs, canonical count boundaries, duplicates, invalid transitions, missing dependencies, concurrent delivery, paths with spaces, permission failures, no-mutation on rejection.
