# state-archive — task-00-sensitive-data-scrub

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Remove private client, employer, system, and machine details from the working tree and add a repeatable public-hygiene check before further publication.

### Affected Parts
Shell scripts and path defaults, workflow and rule examples, operating and historical documentation, templates, local knowledge-base context, and contract validation.

### Codebase Analysis
Discovery context loaded: memory/architecture.md, memory/state.md, principles/architecture.md, principles/coding.md, principles/domain.md, adr/index.md, context/environment.md, context/integrations.md, and context/runbook.md.
Preflight passed: clean tracked working tree, untracked knowledge base, main resolves and is the remote default, origin configured, GitHub authentication succeeds, no existing feature branches or task state.
The repository already has an initial commit; historical notes claiming otherwise are stale. No history rewrite is authorized by this spec.
Files read: 0/12 additional source files. Context describes the affected modules; targeted inventory searches will locate occurrences without re-reading those implementations.

### Open Questions
Two contradictions require the Discovery batch gate: scan exceptions and the timing of the first local commit.


## Archived Solution Design — Variants
1. Extend the existing Bash contract validator with a configurable root denylist and scrub its whole input surface with a final whole-tree atomic cycle. Advantage: one deterministic gate and no new runtime. Disadvantage: broad editorial diff. Risk: self-matches need the explicit batch-gate decision.
2. Add a separate Python hygiene tool and integrate it into the shell validator. Advantage: easier structured handling of filenames. Disadvantage: an unnecessary new runtime and duplicated entry point. Risk: inconsistent scanner behavior.
3. Perform manual replacements only. Advantage: minimal implementation. Disadvantage: fails the required persistent regression guard; rejected as infeasible.


## Archived Solution Design — Rejected
Separate runtime: unnecessary dependency for the required existing validator group. Manual-only cleanup: omits the mandated guard. Unscoped multi-branch cleanup: a global hygiene gate cannot be required to pass on an intermediate partial cleanup; earlier leaves use scoped smoke criteria and the final leaf owns the global gate. Publishing intermediate branches is subject to the explicit batch decision.
