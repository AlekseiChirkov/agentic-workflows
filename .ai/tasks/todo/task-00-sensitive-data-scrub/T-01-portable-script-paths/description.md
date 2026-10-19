## Goal
Portable script path defaults.

## Context
- Dependencies: none.
- Constraints: Follow the recorded user decisions: local commits only; approved scan exclusions; preserve and include the full knowledge base. Follow the smoke test level and report RED before implementation. Write no shared context, logs, or git state; return shared-file deltas to the Orchestrator.
- Reason: One independently verifiable component of the final hygiene contract.

Off-limits: Run-log contents, local settings, deployments, history rewriting, source spec, public rename, environment-variable renaming, and unrelated workflow semantics.

## Scope
- **In scope:** Private path defaults and usages in shell scripts; preserve all existing override names and supported invocation behavior.
- **Out of scope:** Other leaves, history rewriting, credential detection, deployment, new publication authorization, and direct shared-context writes.
- **Target files:** sync.sh, log-step.sh, setup-new-project.sh, setup-umbrella.sh, setup-all-repos.sh, link-skills.sh, scoped smoke checks in validate-contracts.sh.

## Steps
1. Read the approved batch decisions and inventory private script paths and override precedence.
2. Add scoped smoke checks that detect private defaults and exercise relocated paths without deploying; run them and report RED before cleanup.
3. Resolve default roots from script location and retain supported environment overrides; replace private usage examples.
4. Run Bash syntax and relocation/override scenarios, including paths with spaces, without writing outside temporary fixtures.
5. Report GREEN, changed paths, test evidence, and shared-context deltas; perform no git operations.

## Acceptance Criteria
- AC-1: Scoped smoke checks fail before changes because the scripts contain private defaults, then pass unchanged after cleanup.
- AC-2: Every affected script resolves safe default roots and preserves existing environment-variable overrides, including relocated checkouts with spaces.
- AC-3: Bash syntax passes; no deploy, logs, machine settings, source spec, or unrelated workflow behavior changes.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - AC-1 → Verify: Scoped smoke checks fail before changes because the scripts contain private defaults, then pass unchanged after cleanup.
  - AC-2 → Verify: Every affected script resolves safe default roots and preserves existing environment-variable overrides, including relocated checkouts with spaces.
  - AC-3 → Verify: Bash syntax passes; no deploy, logs, machine settings, source spec, or unrelated workflow behavior changes.
- **Edge cases:** Case variants, benign substring matches, filename spaces, relocation, override precedence, explicit self-exceptions, ignored local context, and failures reported as failures.
