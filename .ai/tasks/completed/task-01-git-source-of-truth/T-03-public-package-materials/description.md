## Goal
Provide the concise public project page, precise local ignore rules, and a setup guide that identifies the Orchestrail checkout and planned version tag. Defer the Apache-2.0 license until the owner supplies exact copyright-holder wording.

## Context
- Dependencies: T-02 establishes the new checkout and configuration paths.
- Constraints: README must be no more than 60 lines, state that versions below 1.0.0 are unstable, describe sync's writes to ~/.claude and ~/.codex, and link to the three specified guides; do not create a placeholder license; identify v0.9.0 as a post-release tag.
- Reason: a new reader needs the supported project identity and a safe way to install it.

Off-limits: do not remove tracked knowledge files, add a broad .ai/ or docs/ ignore rule, merge PRs, create or move release tags, or add an incomplete license.

## Scope
- **In scope:** root README, root and log ignore files, section 4 of the setup guide, and package smoke checks.
- **Out of scope:** LICENSE creation until exact holder wording is supplied, implementation of script behavior, changes to Git history, release tagging, and a GitHub repository rename.
- **Target files:** README.md, .gitignore, logs/.gitignore, docs/USAGE.md, validate-contracts.sh.

## Steps
1. Add smoke checks for required README content and length, ignore behavior, and setup-guide wording.
2. Rewrite the root README to the required public summary and links within the line limit.
3. Record the license deferral in task state; do not add a placeholder LICENSE file.
4. Narrow root ignore rules to local runs, active log metadata, and machine settings; retain a tracked logs/.gitignore where required.
5. Update setup-guide section 4 with the live clone URL, the Orchestrail checkout path, and v0.9.0 as the tag to use after release.
6. Keep the entire .ai/ knowledge base and docs/ eligible for tracking.
7. Run the package checks and the complete contract validator.
8. Review all newly written prose for English and required links.

## Acceptance Criteria
- The root README is at most 60 lines and includes the project purpose, pre-1.0 instability statement, sync destinations, and links to docs/USAGE.md, docs/SPEC-RUN-QUICKSTART.md, and .ai/specs/README.md.
- License creation is recorded as deferred in task state until exact copyright-holder wording is supplied; LICENSE is absent until the owner supplies exact holder wording.
- .gitignore excludes logs/runs/, logs/.active/, and .claude/settings.local.json, and does not ignore .ai/ or docs/.
- docs/USAGE.md section 4 gives the live clone URL, clones to `~/projects/orchestrail`, and identifies v0.9.0 as the tag to use after release.
- No release tag is created or moved during this task; release tagging remains deferred until merge and owner authorization.
- The package smoke checks and full contract validator pass.

## Test Plan
- **Level:** smoke
- **Scenarios:**
  - Check README line count, required instability wording, sync destinations, and links → all are present and line count is at most 60.
  - Check task state records license deferral and LICENSE is absent and task state records the deferral → both conditions pass.
  - Run ignore checks for required local paths and representative .ai/ and docs/ paths → local data is ignored and knowledge/docs remain trackable.
  - Inspect setup-guide section 4 → it contains the live clone URL and Orchestrail destination, and identifies v0.9.0 as the post-release tag.
  - Inspect repository tags before and after the task changes → no release tag is created or moved.
  - Run the complete validator → exits successfully.
- **Edge cases:** README exactly at 60 lines, missing required link, accidental placeholder license, .ai/ accidentally ignored, parent ignore rule masking a required path, unmerged release tag.
