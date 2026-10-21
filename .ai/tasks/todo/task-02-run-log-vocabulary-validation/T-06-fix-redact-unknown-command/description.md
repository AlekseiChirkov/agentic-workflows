## Goal
Redact unknown-command errors while preserving nonblocking helper behavior.

## Context
- Source: approved critical integrated contract finding.
- Unknown commands currently echo arbitrary caller text, including embedded newlines.
- Constraints: preserve the canonical contract, event persistence and valid read-only command semantics.

Off-limits: No historical log access or changes, no documentation/retrospective behavior changes, and no weakening existing tests.

## Scope
- **In scope:** The reported invalid invocation and adjacent argument validation necessary to ensure redacted, terminating behavior; permanent isolated regression coverage.
- **Out of scope:** New commands, vocabulary changes, locking or storage redesign.
- **Target files:** `scripts/log-step.sh`, `scripts/validate-contracts.sh`

## Steps
1. Add a failing isolated focused regression reproducing the finding, with a timeout for any blocking path.
2. Replace the raw unknown-command diagnostic with a stable field/reason diagnostic.
3. Verify valid commands and storage immutability.
4. Run the executable acceptance harness, full contract suite and shell syntax checks.

## Acceptance Criteria
- Unknown command inputs, including control characters, produce exactly one redacted stderr line, no stdout, exit zero and no storage changes.
- Missing-command/help behavior and all valid commands remain unchanged.
- The regression runs permanently through the isolated acceptance harness; the full suite and shell syntax pass.

## Test Plan
- **Level:** smoke
- **Scenarios:** Reproduce the reported invalid invocation; assert exit status, stdout/stderr shape, timeout protection and storage checksums; verify valid neighboring behavior.
- **Edge cases:** Missing operands, flag-shaped operands, repeated/unknown arguments, empty values, newline-bearing caller text and absent storage. Keep all fixtures temporary.
