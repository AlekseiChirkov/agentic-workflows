spec_path: .ai/specs/24-task-finalization.md
flow: full

## Phases
- discovery: complete
- execution: in-progress
- validation: not-started

## Task Analysis
Owner supplied and approved the complete design; requirements are retained in the source specification.

### Assumptions
- Source dependency remains unmerged; implementation starts at its pinned tip without paused audit changes.
- No --allow-pr authorization: all delivery stays local; no push or GitHub mutation.

## Decomposition
decomposition: complete

## Model Selection
selection: complete
Session-default workers; no model or effort override requested. Actual model identity and effort are not independently observed. Preliminary provider recommendations are inapplicable to this explicit default-worker request.

## Solution Design
### Decision
One phase, deterministic evidence/journal/archive helper, explicit Git commands, narrow hook authorization, staged sync. Owner-approved plan of 2026-11-17.
### Scope
One validated development task, all recorded repositories, mandatory cleanup.
### Invariants
No uncertain deletion, no lost protected history, no implicit deployment, no live test mutations.
### Off-limits
Paused audit, consumer installations, PR merging and protected/base publication.
### Acceptance Criteria
The source specification AC-01 through AC-06 apply.

## Subtask Progress
T-01 | Implement evidence, journal and lossless archival mechanics | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: approved scope recorded
  target_files:
  blocker: none
  notes:

T-02 | Enforce scoped cleanup and stage provider outputs | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: approved scope recorded
  target_files:
  blocker: none
  notes:

T-03 | Connect finalization with shared workflow contracts | atomic-tests: not-started | atomic-execution: not-started | atomic-validation: not-started
  last_action: approved scope recorded
  target_files:
  blocker: none
  notes:
