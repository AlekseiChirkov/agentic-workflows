# Bounded tool previews with complete local evidence

## Source

Workstream 6 of the owner's 2026-10-21 request: reduce input from large command, search,
test and file outputs without hiding information needed for a correct result.

## Context & Problem

Current workflows require command evidence and git/test inspections
(`workflows/spec-run.md:182`, `workflows/pav-check.md:92`). An optimization cannot
replace full failures with success-shaped summaries or defeat the git rails in 06.

## Goal

Bound routine tool text entering model context while retaining complete, identifiable,
retrievable local output and the original command result.

## Scope

Optional capture/preview helper, search/file/test output policies, structured summaries,
range retrieval, failure preservation and workflow integration.

## Out of Scope

Suppressing errors, changing commands or assertions, bypassing sandbox approvals,
filtering source code before execution, paid LLM summarization of tool output, or
changing the canonical run-log writer's non-blocking behavior.

## Actors & Roles

The executing role chooses an appropriate supported command. The helper captures local
output and produces a bounded preview. Reviewers can retrieve full evidence/ranges.
The orchestrator retains approval, git and shared-state ownership.

## Terminology

A preview is explicitly incomplete when truncated. An artifact is the full captured
stdout/stderr with exit status and identity. A command outcome is not the helper's
summary verdict.

## Requirements

- **REQ-01** THE SYSTEM SHALL provide optional bounded output for search listings,
  selected source ranges, diffs, compiler/test/lint output and controller inspections.
  It SHALL preserve executable/argument identity, working directory, stdout/stderr,
  original exit code and termination signal where exposed.
- **REQ-02** WHEN capturing, THE SYSTEM SHALL write complete local output before
  presenting a preview, attach an artifact path/content hash and byte/line counts,
  and mark truncation explicitly. Default total preview SHALL be at most 8,192 bytes,
  with configurable positive limits sufficient for mandatory metadata. An undersized
  limit SHALL fail validation before executing the command; line-based display SHALL not silently count
  multibyte characters as bytes or hide an oversized single line.
- **REQ-03** WHEN a command fails, THE SYSTEM SHALL preserve diagnostic locations,
  failing test names and available summary counts in the preview, label any unshown
  diagnostics and provide retrieval. An unrecognized format SHALL use a generic
  bounded head/tail with honest truncation, not guess success or omit stderr.
- **REQ-04** THE SYSTEM SHALL support exact range/full retrieval of an artifact,
  preserving its hash and original bytes. A missing, changed or unreadable artifact
  SHALL invalidate the evidence reference and trigger recapture or explicit failure,
  not silently reuse a prior success.
- **REQ-05** WHEN selecting search/file output, THE SYSTEM SHALL use targeted queries,
  names-first discovery and relevant ranges where sufficient, preserve no-match versus
  command-failure status, and request expansion when interface/AC evidence is missing.
  No fixed first-N-file rule SHALL be treated as completeness.
- **REQ-06** THE SYSTEM SHALL avoid unsafe shell string interpolation: command capture
  SHALL use argument arrays/no eval, and pipelines/redirections SHALL use an explicitly
  reviewed script or existing supported shell invocation. If a wrapper would hide the
  command from a permission/git-rail hook, it SHALL NOT wrap that command; use native
  execution/output limits with separate evidence capture instead.
- **REQ-07** THE SYSTEM SHALL keep artifacts local, out of committed product code,
  with restrictive permissions and a documented retention/cleanup policy preserving
  active task/review evidence. Failure to capture a complete output SHALL be explicit;
  fallback native execution SHALL not run a mutating command twice.
- **REQ-08** THE SYSTEM SHALL attach output/preview sizes and retrieval counts to 05,
  retain failure exit codes for CI/gates, and apply shared index gates G1–G8.
  A shorter preview SHALL not be described as lower API cost without measurement.

## Data Model

Artifact ID/path, command argv digest, allowed working directory, timestamp, tree hash
where meaningful, original return status/signal, stdout/stderr hashes and byte counts,
preview bounds/truncation and diagnostic extraction confidence. Raw commands/output may
contain private data and stay local; exported telemetry uses safe metadata only.

## Contracts & Interfaces

Proposed optional interface:
`scripts/capture-output.sh --limit-bytes <N> --artifact-dir <dir> -- <command> [args...]`
and a read-only range/full-output subcommand. The execution mode returns the original
command's exit status when capture succeeds. If capture fails after a successful
command, it returns helper status 125 and reports the original status separately;
if the command also failed, its original nonzero status takes precedence. Capture
failure is always explicit, never a passing evidence receipt.
A signal is not translated into success. Helper failure must not rerun a command
whose side effects may already have happened. Existing CLI-specific exit contracts
remain visible, including log-step's deliberate best-effort zero.

The helper never broadens permissions; 06 must still see protected git commands.
Native harness truncation is acceptable only with complete retrievable evidence.

## Non-Functional Requirements

Default preview ≤8,192 bytes including metadata/markers; exact full output retained.
Capture uses streaming/spooling so large output need not reside wholly in memory.
No network/model call, no eval, no arbitrary cleanup outside the artifact root.

## Edge Cases & Failure Modes

Cover empty output, exact limit/limit+1, huge single line, UTF-8 split boundaries, binary
output, stderr-only failure, missing executable, exit 1 no-match, compiler/test formats,
signal/timeout, disk full, interrupted capture, artifact mutation and unsafe wrapper
visibility. A failed mutation is inspected before any retry.

## Acceptance Criteria

- [ ] **AC-01** (REQ-01, REQ-02) Synthetic success/failure outputs preserve argv, streams
  and exact return status; 0/boundary/oversized/UTF-8 fixtures respect total preview
  bounds and full artifact hashes match original bytes.
- [ ] **AC-02** (REQ-03, REQ-05) Failing tests, stderr-only errors, generic formats and
  no-match searches are distinguished; incomplete context requests retrieve more data.
- [ ] **AC-03** (REQ-04) Full/range retrieval reproduces bytes; missing or edited artifacts
  cannot satisfy a verification evidence reference.
- [ ] **AC-04** (REQ-06, REQ-07) Adversarial argv/shell characters execute literally;
  protected git commands remain visible to rails or are refused by the wrapper;
  simulated capture failure executes a side-effect counter command only once.
- [ ] **AC-05** (REQ-07, REQ-08) Local retention/privacy, fallback and disable instructions
  exist; telemetry records preview/full/retrieved bytes separately and offline checks
  cannot convert a failing original command into a passing gate.

## Traceability

| Requirement | Acceptance |
|---|---|
| REQ-01, REQ-02 | AC-01 |
| REQ-03, REQ-05 | AC-02 |
| REQ-04 | AC-03 |
| REQ-06 | AC-04 |
| REQ-07 | AC-04, AC-05 |
| REQ-08 | AC-05 |

## Risks

Useful diagnostics can occur anywhere in a large output. Preview caps require honest
truncation, reliable full retrieval and impact-driven expansion; they are not a proof
that a reviewer has seen enough.

## Assumptions

Local writable evidence storage is usually available. Without it, preserve correctness
through native output/retrieval and record that bounded capture was unavailable.

## Decisions

Keep optional local tools, native approval enforcement and complete evidence.
Do not change production run budgets or replace deterministic tools with another LLM.

## Clarifications

2026-10-21: the 8 KiB default is a configurable preview policy, not a measured optimum
or a cap on failures/evidence available to an agent.

## Open Questions

None blocking. Optimal caps and retrieval overhead require later measured evaluation.

## Notes

Depends on 06, 09 and 14. Suggested slices: streaming capture; previews; diagnostics;
retrieval/retention; safe workflow integration; deterministic tests/docs.

## Readiness Checklist

Interface, limits, exit behavior, error preservation, security boundaries and acceptance
are explicit. Ready for Discovery; savings unmeasured.
