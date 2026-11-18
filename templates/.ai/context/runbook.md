# runbook.md — operational procedures and recovery steps

## Purpose
Step-by-step procedures for routine and incident-time operations: deploys,
rollbacks, recovery from common failures, on-call playbooks. The agent
consults this when an incident or operational task is in scope. Answers
"how do I operate this system safely?" Updated when a procedure changes or
a new incident teaches a new recovery path.

## Commands
Required for test/lint automation — fill in after project setup
test:      <command to run full test suite>     e.g. pytest tests/ -v
lint:      <command to run linter>              e.g. ruff check src/
typecheck: <command for type checking>          e.g. mypy src/ (optional)
build:     <command to build>                   e.g. docker build -t app . (optional)

## Structure

## Procedures
One subsection per procedure: name, when to use, prerequisites, steps,
verification.

### Post-merge task finalization

Use `/phase-finalize <task-directory|spec-path> [--dry-run]` after owner integration.
Record required checks and any permitted prior-evidence reuse with source revisions and
coverage/runtime limits. Retain failed checks and recovered teardown attempts. State any
required deployment explicitly in the spec Delivery Contract; proof needs a dated source
revision and environment. Missing proof is unverified, never inferred from task closure.
Keep recovery material and stable journals under `.ai/context/finalization/` according to
repository tracking policy. Do not commit untracked consumer or umbrella state by default.
