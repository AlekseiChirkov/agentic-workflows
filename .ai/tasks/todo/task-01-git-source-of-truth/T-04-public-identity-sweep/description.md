## Goal
Remove the former project identity from all mutable repository content and verify the approved exact source, history, and public clone URL exceptions with a scoped final scan.

## Context
- Dependencies: T-03 establishes the final package name, public paths, the live repository clone URL, and the approved scan exceptions.
- Constraints: preserve all knowledge files; keep the active source specification immutable; preserve only the enumerated historical matches; do not rename the public GitHub repository; never add private absolute paths or denylisted personal identifiers.
- Reason: the public name must be consistent across workflow instructions, templates, and the tracked knowledge base while preserving source and history.

Off-limits: do not rewrite completed implementation history, delete historical records, change user-facing behavior beyond the approved name and path updates, or broaden the scan exceptions beyond the exact lines and URL token recorded in task state.

## Scope
- **In scope:** remaining current references in scripts, instructions, templates, rules, workflows, principles, context, roadmap, setup documentation, and task memory, plus exact matches listed in task state.
- **Out of scope:** rewriting historical analysis, audit, ADR, and completed-task records; renaming the public GitHub repository; rewriting Git history; changing the active source specification.
- **Target files:** CLAUDE.md, README.md, docs/README.md, docs/USAGE.md, link-skills.sh, setup-all-repos.sh, setup-new-project.sh, setup-umbrella.sh, sync.sh, validate-contracts.sh, templates/.ai/principles/architecture.md, templates/codex-global-AGENTS.md, workflows/pv-create-fixes.md, .ai/README.md, .ai/adr/index.md, .ai/context/runbook.md, .ai/memory/architecture.md, .ai/memory/state.md, .ai/principles/architecture.md, .ai/specs/README.md, .ai/specs/13-model-only-harnesses-and-rule-naming.md.

## Steps
1. Add a smoke check for the no-former-name criterion using a constructed search term so the validator does not contain the prohibited literal itself.
2. Apply the exact task-state ledger; compare every `(path, line, token, count)` entry, including per-token counts on each approved line, and fail on unmatched hits, missing expected hits, or any extra token on an approved line.
3. Replace remaining current identity references in scripts, root instructions, and templates.
4. Update remaining rules and workflows that describe the repository by its former name.
5. Update mutable knowledge-base introductions, the roadmap, setup documentation, and current task memory.
6. Preserve only the exact historical line matches and the public slug inside the live clone URL; continue scanning all local checkout paths.
7. Run the scoped name scan, public-hygiene validator, full contract validator, and Bash syntax checks.
8. Record scan scope, counts, and each exact retained match in task state.

## Acceptance Criteria
- All mutable current-content references use the Orchestrail identity and approved configuration paths.
- The scoped scan finds no former-name matches outside the exact line locations and single clone-URL token recorded in Approved Identity Scan Exceptions in task state.
- The existing public-hygiene check still passes and no tracked knowledge-base file is deleted.
- Task state records the exact scan scope, counts, and retained matches without copying sensitive denylist contents.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - Search the required roots, scripts, and knowledge-base scope with the constructed former-name term → every `(path, line, token, count)` matches the task-state ledger, including exact per-token counts on approved lines and the single public-slug token in the live clone URL.
  - Compare the tracked knowledge-file inventory before and after → every baseline path remains present.
  - Run the public-hygiene and full contract validators → both exit successfully.
  - Run Bash syntax checks on all root scripts → all pass.
  - Inspect task state scan ledger → every exception has an exact file, line, token, and occurrence count; no directory-wide exclusion exists.
- **Edge cases:** case differences, underscore and hyphen spellings, Markdown links, mutable future specs, exact source-spec self-reference, historical ADRs and analysis, completed pull-request links, live clone URL, old local paths, symlink text.
