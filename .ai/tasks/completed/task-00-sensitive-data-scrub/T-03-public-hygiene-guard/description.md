## Goal
Public hygiene scanner and final sweep.

## Context
- Dependencies: T-02.
- Constraints: Follow the recorded user decisions: local commits only; approved scan exclusions; preserve and include the full knowledge base. Follow the smoke test level and report RED before implementation. Write no shared context, logs, or git state; return shared-file deltas to the Orchestrator.
- Reason: One independently verifiable component of the final hygiene contract.

Off-limits: Run-log contents, local settings, deployments, history rewriting, source spec, public rename, environment-variable renaming, and unrelated workflow semantics.

## Scope
- **In scope:** Configurable root denylist, tracked-file hygiene group, remaining corpus redactions, full knowledge-base inclusion without deleting files, local-context cleanup deltas, and final manual sweep under the approved exceptions.
- **Out of scope:** Other leaves, history rewriting, credential detection, deployment, new publication authorization, and direct shared-context writes.
- **Target files:** validate-contracts.sh, scrub-denylist.txt, .gitignore, README.md, remaining affected rules/workflows/templates/documents; return mutable local-context redactions as shared-file deltas.

## Steps
1. Read the approved scan exceptions and publication decision; inventory remaining private tokens including benign substring matches.
2. Add the configurable hygiene check and public-hygiene denylist before remaining cleanup; run on the current tree and report the expected RED digest.
3. Clean the remaining tracked corpus without changing unrelated semantics and return exact mutable local-context deltas to the Orchestrator.
4. Exercise tracked contamination, case variants, filenames with spaces, empty tracked input, exclusions, and scanner-error behavior in temporary fixtures.
5. Run the complete existing contract suite with every original check preserved; re-run after the Orchestrator applies shared deltas.
6. Execute the agreed manual sweep and record command, exact exclusions, exit status, zero-match evidence, and unchanged local-store ignore status.

## Acceptance Criteria
- AC-1: The new hygiene check observes a genuine private-token failure before final cleanup and succeeds afterward; every tracked file except approved exceptions is scanned with literal case-insensitive patterns.
- AC-2: The denylist documents public hygiene rather than secret storage and requires same-change cleanup; synthetic contamination, case variants, space-containing filenames, and scanner errors have the expected outcomes.
- AC-3: The final approved manual sweep finds no unexpected tokens after local-context deltas are applied; logs and local settings remain ignored and unmodified.
- AC-4: The full existing contract suite passes with original checks intact and exact final scan evidence recorded locally.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - AC-1 → Verify: The new hygiene check observes a genuine private-token failure before final cleanup and succeeds afterward; every tracked file except approved exceptions is scanned with literal case-insensitive patterns.
  - AC-2 → Verify: The denylist documents public hygiene rather than secret storage and requires same-change cleanup; synthetic contamination, case variants, space-containing filenames, and scanner errors have the expected outcomes.
  - AC-3 → Verify: The final approved manual sweep finds no unexpected tokens after local-context deltas are applied; logs and local settings remain ignored and unmodified.
  - AC-4 → Verify: The full existing contract suite passes with original checks intact and exact final scan evidence recorded locally.
- **Edge cases:** Case variants, benign substring matches, filename spaces, relocation, override precedence, explicit self-exceptions, ignored local context, and failures reported as failures.
