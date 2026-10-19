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
