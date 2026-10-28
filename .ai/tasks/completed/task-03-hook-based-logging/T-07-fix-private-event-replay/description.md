# Preserve private producer acceptance across replay and ordinary writes

## Goal

Reject malformed cached acceptance without changing storage, retain private active metadata across every writer, and preserve the documented step-name advisory on new correlated writes.

## Context

- Dependency: T-06 and the complete reviewed stack.
- Source: the owner's additional independent per-PR validation request on 2026-10-26; PR23 review found two important defects and one optional advisory regression.
- Arbiter decision: one appended producer repair; validate fresh private JSON before numeric conversion, establish restrictive permissions before temporary-file creation, and distinguish intentional session `unknown` from arbitrary unrecognized names.

## Scope

Product scope: scripts/log-step.sh. Add regression assertions to the existing isolated producer acceptance area in scripts/validate-contracts.sh; retain every frozen assertion and the focused source contract. Root owns knowledge, git, commits, pull requests and integration records.

Do not change historical mathematical-integer lint compatibility, event-log permissions, ordinary optional-jq behavior, attribution, delivery ownership, rollback order, public payload vocabulary or dependencies. Do not read historical logs for acceptance or deploy to real settings.

## Steps

1. Freeze failing cases for malformed cached sequence values, mixed ordinary/correlated metadata updates under permissive umasks, and new correlated step-name advisories. Report RED and wait for the test-only commit.
2. Reject literal NUL before line-oriented metadata reading, then validate one complete cached JSON object with matching argument object and raw canonical positive bounded sequence before returning a duplicate receipt. Reject malformed state with a safe warning, no receipt and unchanged storage; preserve valid escaped JSON and literal percent text.
3. Create active metadata temporary files privately before redirection and retain mode 0600 across ordinary and correlated updates without affecting event files or adding jq to ordinary writes.
4. Restore the advisory after newly accepted correlated writes, preserving valid session unknown, duplicate idempotence, rejected-write diagnostics and receipts.
5. Run the full focused producer, adapter, source-quality and canonical checks; independently review the repair and execute the final cumulative gate.

## Acceptance Criteria

- Zero, exponent, negative, fractional, string, boolean, oversized, literal-NUL-bearing, malformed or multiple cached JSON values cannot establish acceptance; canonical positive bounded sequences still replay without appending or mutating metadata. Check raw bytes before Bash can discard NUL; valid escaped JSON, percent text and legacy newlines remain compatible.
- Under umasks 000 and 002, accepted metadata followed by ordinary updates remains mode 0600, including temporary creation; ordinary no-jq logging remains functional and event-log permissions are unchanged.
- Newly accepted arbitrary unrecognized correlated step names retain the supplied text, return a valid receipt and emit the documented single advisory. Known names and intentional session unknown remain compatible; rejected and duplicate deliveries produce no new advisory.
- All original frozen assertions remain intact. New functions meet focused size and parameter limits; producer, adapter, source quality, canonical and cumulative validation pass with disposable settings and log stores.

## Test Plan

Level: integration and contract. Map raw cache and no-mutation probes to the first criterion, permissive umask/mixed-route/no-jq probes to the second, advisory/known/unknown/replay probes to the third, and frozen-suite/source-contract checks to the fourth. No live model or historical telemetry access.
