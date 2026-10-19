# ADR-0010: Decisions for Task unknown — Public hygiene and local publication

## Status

Accepted

## Date

2026-10-19

## Related Task

- Task: [Sensitive-data scrub](../tasks/todo/task-00-sensitive-data-scrub/state.md)
- Related files: `validate-contracts.sh`, `scrub-denylist.txt`, `.gitignore`, source and log helpers

## Summary

Use the existing contract validator to enforce literal public-hygiene patterns, preserve and track the entire knowledge base, and withhold remote publication until existing history receives a separate remediation decision.

## Context

The repository already has an initial commit containing private references. Cleaning descendants cannot remove ancestor contents. The owner explicitly chose local test-first commits, no pushes or pull requests, and preservation and inclusion of every knowledge-base file. A plaintext pattern list and its original source requirement necessarily retain the listed strings.

## Decisions

### Decision 1: Exact scan exceptions with fail-closed tracked-file checks

**What was decided:**
Scan current contents of every indexed path using case-insensitive literal substring matching. Exempt only the root pattern list and the original source requirement. Read symlink target text rather than accessing targets outside the repository. Missing or unreadable inputs, scan errors, and an empty index fail; empty ordinary files remain valid. The manual sweep additionally excludes Git internals, local logs, and the local machine settings file.

**Why:**
This makes the hygiene criterion satisfiable without hiding mutable content or treating scanner errors as clean results. The implementation is at `validate-contracts.sh:11`; exact automatic exceptions are at `validate-contracts.sh:44`.

**Alternatives:**
Manual-only cleanup omits the required regression guard. Word-boundary matching changes the owner's literal substring requirement. Blanket directory exemptions would hide knowledge-base data.

**Consequences:**
Adding a public-hygiene token requires same-change cleanup. The list is not a credential store. A standalone scanner uses the same implementation as the full suite (`validate-contracts.sh:68`).

### Decision 2: Preserve and track the complete knowledge base

**What was decided:**
Retain every existing file and anonymize mutable contents in place. Include the full directory in this source repository. The owner explicitly overrides the consumer-repository exclusion for this repository; reusable consumer defaults remain unchanged.

**Why:**
The knowledge base is contributor documentation and the owner expressly required its complete inclusion. `.gitignore:1` retains logs and `.gitignore:2` retains machine settings while permitting knowledge-base tracking.

**Alternatives:**
Deleting context or continuing to exclude it contradicts the owner's instruction. Tracking only selected subdirectories would omit the required audit record.

**Consequences:**
This implements the existing repository-specific decision in ADR-0007. Future runs must honor the owner's repository exception when reconciling tracked task state. A final state snapshot cannot contain its own hash; its parent and permitted paths are recorded before committing, and its hash is reported separately.

### Decision 3: Local commits with remote publication withheld

**What was decided:**
Allow separate local test and implementation commits. Perform no pushes, pull requests, merges, or history rewrites. Remote publication awaits a separately authorized history-remediation decision.

**Why:**
The existing ancestor already contains private references. Publishing a cleaned descendant still exposes that ancestor. The owner selected this approach explicitly.

**Alternatives:**
Publishing after a clean working-tree sweep does not meet clean-history intent. Rewriting existing history is outside this change and is not authorized.

**Consequences:**
This amends only the pre-initialization timing clause of ADR-0009 Decision 1 for the already initialized repository. Its other roadmap decisions remain accepted. Local changes are reviewable without expanding remote exposure.

### Decision 4: Portable defaults with existing configuration names

**What was decided:**
Derive script defaults from their locations while retaining current source and log-root overrides. Normalize the selected umbrella source before invoking service setup. Keep the public rename outside this change.

**Why:**
Private machine paths must not return through source defaults. Script-root resolution is implemented at `sync.sh:6` and `log-step.sh:31`; the log override remains at `log-step.sh:32`.

**Alternatives:**
Replacing one personal absolute path with another retains leakage. Renaming configuration variables here duplicates the later identity change.

**Consequences:**
Relocated paths, spaces, environment overrides, and child source propagation have regression coverage. Existing consumers retain their configuration names.

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| Which scan exceptions are accepted? | Root list, source requirement, Git internals, local logs, and local settings according to their scan scope | Keep all mutable context within the manual sweep |
| Should the knowledge base be removed or excluded? | Preserve every file and include the full directory | Remove only the ignore rule; anonymize contents in place |
| May commits precede the final sweep? | Local test-first commits are permitted | Retain separate observed-failure commits |
| May the cleaned stack be pushed? | No; wait for separate history remediation | Keep all branches and review artifacts local |

## Rejected Options

Automatic history rewriting, publication of existing private ancestry, broad scan exemptions, knowledge-base deletion, and configuration renaming in this change.

## Implications for Future Work

Resolve existing history before any remote publication. Preserve this source-repository tracking exception without weakening consumer defaults. Repair the unrelated pre-existing umbrella-template relative path in a separate focused change.

## Verification

Independent atomic and task validation passed: 542 contract/smoke checks, Bash syntax, frozen-test audits, 23 contract requirements, full indexed hygiene including 45 knowledge files, and a 152-file manual sweep with zero unexpected matches/errors. All 44 baseline knowledge paths are preserved. One optional test-fixture refinement is deferred. Main and existing history remain unchanged; no push, PR, merge, or deployment occurred.

## Publication Amendment — 2026-10-19

After validation, the owner requested pull requests and explicitly approved publication to AlekseiChirkov/agentic-workflows with private references in existing ancestry and approved scan exceptions retained. This supersedes Decision 3's remote-publication hold and the historical publication restrictions above. It authorizes additive branch pushes and pull requests only; no merge, force push, branch deletion, main update, deployment, or history rewrite is authorized.

The three branches were published and their drafts promoted to ready after validation. Merge order is [#2](https://github.com/AlekseiChirkov/agentic-workflows/pull/2), then [#3](https://github.com/AlekseiChirkov/agentic-workflows/pull/3), then [#4](https://github.com/AlekseiChirkov/agentic-workflows/pull/4). Existing ancestry remains unchanged. Earlier verification statements describe the local validation checkpoint before this amendment.

## References

- Task: [Local state](../tasks/todo/task-00-sensitive-data-scrub/state.md)
- Pull requests: #2, #3, and #4 ready for review; see the publication amendment
- Related documents: ADR-0007, ADR-0009, user answers of 2026-10-19
