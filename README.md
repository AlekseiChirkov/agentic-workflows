# agentic_workflows

A configurable development process for AI coding assistants: turn a specification
into tested changes, independent review, and pull requests while preserving project
context between sessions.

The goal is to make AI-assisted engineering more predictable and reviewable.
Requirements, boundaries, decisions, test results, and progress are recorded on
disk so that a task can continue beyond a single conversation.

## How it works

The main delivery cycle is:

```text
Specification -> Discovery -> Tests and implementation -> Validation -> Human review
```

1. **Discovery:** analyze the existing code, define acceptance criteria and
   boundaries, split the work, and choose an implementation approach. Unresolved
   product questions are collected for a human decision before implementation.
2. **Execution:** establish failing tests before changing behavior, implement until
   they pass, and record the evidence. The process also defines characterization
   tests for behavior-preserving work and justified exemptions from testing.
3. **Validation:** check the result against the requirements, review the code, and
   track necessary fixes. In the full delivery workflow, a separate reviewer works
   without the implementer's conversation history.
4. **Delivery:** prepare dependent branches and pull requests that can be reviewed
   incrementally. Publishing requires explicit opt-in; merging stays with the human.

Small eligible changes have a shorter path that retains requirements, testing
decisions, and review. Existing projects can be onboarded into a persistent
knowledge base. Groups of service repositories can share architectural context
and standards while keeping local details in each repository.

## What the repository provides

| Component | Responsibility |
| --- | --- |
| `workflows/` | Instructions for planning, implementation, validation, delivery, and maintenance. |
| `rules/` | Shared contracts for testing, state transitions, escalation, Git operations, and collaboration. |
| `principles/` | Engineering standards that can be adapted to the project's stack and domain. |
| `templates/` | Starting structures for project instructions, specifications, and knowledge bases. |
| Setup and sync scripts | Install the instructions into supported tools and initialize consuming projects. |
| Validation scripts | Check consistency between workflow definitions and check the artifacts produced for a task. |
| Run logging | Record outcomes and timing for later inspection and process improvement. |

Deployment targets include Claude Code, Codex, and Windsurf/Devin Desktop.
Installing the instructions does not guarantee identical execution capabilities:
the full delivery workflow needs a host that supports the required agent roles,
context isolation, and messaging.

## Comparison with alternatives

Comparison checked on **October 19, 2026**, using the official sources linked below.
Selection guidance is an assessment of the documented approaches, rather than a
benchmark of delivery speed, cost, or defect rates. Extensions and configuration
can change what each alternative supports.

| Solution | Main approach | When it is the better starting point | Why choose agentic_workflows instead |
| --- | --- | --- | --- |
| **[GitHub Spec Kit](https://github.com/github/spec-kit)** | Specification-driven delivery with reusable templates, processes, extensions, presets, and workflow automation. | You want an extensible toolkit and prefer assembling a process from its supported components. | You want the particular testing, independent validation, recovery, and dependent-PR policies already defined here. |
| **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** | A lightweight specification layer with proposals, requirements, designs, task lists, and archived changes; artifacts can evolve without rigid phase gates. | You want flexible specification management with a small amount of process around implementation. | You need explicit phase contracts, testing evidence, and a prescribed review and delivery sequence. |
| **[BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD)** | A development method spanning product analysis, requirements, architecture, and implementation, with specialized roles and workflows. | Product discovery and deciding what to build are a large part of the work. | Your priority is a detailed engineering process for executing scoped requirements through tests, validation, and incremental PRs. |
| **[Superpowers](https://github.com/obra/superpowers)** | Composable engineering skills covering design, plans, TDD, isolated workspaces, implementation, and review. | You want a ready-made engineering methodology with substantial overlap in testing and review practices. | You specifically need this repository's shared knowledge structure, recorded recovery procedure, and dependent-branch delivery policy. |
| **[Kiro](https://kiro.dev/docs/specs/)** | An integrated environment with requirements, designs, task tracking, and parallel execution of independent tasks. | You want built-in task execution and progress tracking within a supported product. | You want to own and edit the process as repository files and distribute its instructions across your existing tools. |

TDD and independent review are shared ideas, especially with Superpowers. The
distinction is the combination and specificity of the policies here. Adopting this
project means maintaining that combination yourself.

## When to choose this project

Choose agentic_workflows when several of these needs occur together:

- **Long-lived project context:** architecture, conventions, decisions, and active
  work must survive session changes and developer handoffs.
- **Explicit engineering boundaries:** changes need documented acceptance criteria,
  existing invariants, and areas the implementation must leave untouched.
- **Reviewable evidence:** reviewers need recorded testing decisions and an
  independent assessment of whether the requirements were met.
- **Incremental delivery:** larger changes should arrive as dependent branches and
  focused pull requests, with a defined way to update the remaining stack after merges.
- **Shared standards across repositories:** related services need common context
  with local overrides. Execution still uses a separate specification per repository.
- **Ownership of the process:** someone on the team can maintain the instructions,
  adjust engineering standards, and validate changes to the workflow contracts.

For example, an established backend spanning several service repositories may
benefit from shared architectural knowledge, tests before behavior changes, a
separate review per implementation unit, and a controlled sequence of PRs. This
project packages those requirements into one process.

## Tradeoffs and reasons to choose an alternative

- **Instructions need an executor.** Most sequencing and safety policies are
  Markdown instructions interpreted by the coding assistant. The shell validators
  check selected contracts and artifacts; they do not enforce every action during
  a run. Permissions, CI, and branch protection remain separate mechanisms.
- **The process has overhead.** Loading context, writing artifacts, and running
  separate reviews consume time and model tokens. This repository provides no
  comparative performance or cost guarantee.
- **Full execution is sequential.** Agent separation limits context and separates
  responsibilities; it does not provide parallel implementation of independent
  tasks. Prefer a system with built-in parallel execution if that is decisive.
- **Setup needs adaptation.** Several scripts assume a particular checkout location
  under the user's home directory. Engineering principles include stack-specific
  standards that should be reviewed before adoption.
- **Local knowledge needs ownership.** Task and knowledge artifacts are excluded
  from version control by the current policy. Team sharing, backup, and recovery
  require an explicit arrangement.

For a short prototype or a team seeking minimal setup, OpenSpec or a ready-made
Superpowers installation may be a better fit. For integrated task execution, assess
Kiro. For a broadly extensible process foundation, assess Spec Kit. For extensive
product discovery, assess BMAD Method.

## Further reading

- [Operating manual](docs/USAGE.md): setup, project initialization, and daily commands.
- [Delivery quickstart](docs/SPEC-RUN-QUICKSTART.md): prerequisites, execution,
  recovery, and pull request handling.
- [Documentation index](docs/README.md): manuals, audits, and analysis.

For exact behavior, check the current workflow definitions and scripts alongside
the manuals. The comparison above describes the default documented approaches;
it does not claim that an alternative cannot be configured to meet the same needs.
