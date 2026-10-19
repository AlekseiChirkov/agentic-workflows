# state.md — cross-service tasks and active work

## Purpose
Tracks tasks that span multiple service repositories.
Single-service tasks belong in the service's own .ai/memory/state.md, not here.
Updated when a cross-service task changes phase or status.

## Structure

## Cross-Service Tasks
One entry per task: name, affected services, current phase, status, link to spec and task directory.

Format:
```
### <task-name>
- spec: .ai/specs/<NN>-<slug>.md
- task: .ai/tasks/todo/<task-slug>/
- phase: discovery | execution | validation | complete
- status: in-progress | blocked | complete
- repos: service-api, service-worker, ...
- notes: <any relevant context>
```

## Deferred
Cross-service work explicitly postponed, with reason and affected services.

## Blocked
Cross-service tasks waiting on external dependency or inter-service contract.
