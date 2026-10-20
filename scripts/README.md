# Repository scripts

All executable shell helpers live in this directory. Run project setup helpers from the
target project or umbrella directory. `sync.sh` and setup helpers resolve this repository
root from the parent of `scripts/`, unless `ORCHESTRAIL_HOME` selects another checkout.
`sync.sh --from` takes precedence over `ORCHESTRAIL_HOME`.

| Script | Purpose |
|---|---|
| `sync.sh` | Validate and deploy workflows, rules, and principles to supported coding assistants. |
| `setup-new-project.sh` | Initialize one consumer project. |
| `setup-umbrella.sh` | Initialize shared context for a multi-repository project. |
| `setup-all-repos.sh` | Initialize service repositories under an umbrella. |
| `link-skills.sh` | Link global Claude skills into a project that has local skills. Run from that project. |
| `log-step.sh` | Append pipeline run and step events to the local log store. |
| `validate-contracts.sh` | Check repository-wide workflow contracts. |
| `validate-task.sh` | Validate one task directory passed as an argument. |
