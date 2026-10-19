## Goal
Neutral public examples.

## Context
- Dependencies: T-01.
- Constraints: Follow the recorded user decisions: local commits only; approved scan exclusions; preserve and include the full knowledge base. Follow the smoke test level and report RED before implementation. Write no shared context, logs, or git state; return shared-file deltas to the Orchestrator.
- Reason: One independently verifiable component of the final hygiene contract.

Off-limits: Run-log contents, local settings, deployments, history rewriting, source spec, public rename, environment-variable renaming, and unrelated workflow semantics.

## Scope
- **In scope:** Umbrella, quick-gate, workflow, operating, analysis, and audit examples derived from private projects; use fictional examples and English replacement prose.
- **Out of scope:** Other leaves, history rewriting, credential detection, deployment, new publication authorization, and direct shared-context writes.
- **Target files:** docs/USAGE.md, templates/.ai-umbrella/README.md, rules/quick-flow.md, rules/workflow-reference.md, workflows/retro.md, affected historical analysis/audit documents and templates, scoped smoke checks in validate-contracts.sh; scrub-denylist.txt may be introduced as shared test input if needed.

## Steps
1. Read the batch decisions and inventory example-specific private strings and existing teaching outcomes.
2. Add scoped smoke checks for the specified public examples; run and report expected RED before replacing them.
3. Use the acme-platform umbrella and fictional system names consistently, retaining rejected multi-file behavior changes and accepted single-file log-level changes.
4. Redact historical project and internal-source names with Project A/B/C and an English legend; preserve unrelated existing prose.
5. Run unchanged scoped checks and manually verify teaching outcomes; report GREEN and return shared local-context deltas.

## Acceptance Criteria
- AC-1: Scoped public-example checks fail before redaction and pass afterward with the same assertions.
- AC-2: The umbrella examples use acme-platform with service-api, service-worker, service-frontend, and infra; the quick-gate examples preserve their accepted/rejected outcomes.
- AC-3: Affected public documents contain no example-specific private identifiers or internal-source details; new replacement prose and labels are English.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - AC-1 → Verify: Scoped public-example checks fail before redaction and pass afterward with the same assertions.
  - AC-2 → Verify: The umbrella examples use acme-platform with service-api, service-worker, service-frontend, and infra; the quick-gate examples preserve their accepted/rejected outcomes.
  - AC-3 → Verify: Affected public documents contain no example-specific private identifiers or internal-source details; new replacement prose and labels are English.
- **Edge cases:** Case variants, benign substring matches, filename spaces, relocation, override precedence, explicit self-exceptions, ignored local context, and failures reported as failures.
