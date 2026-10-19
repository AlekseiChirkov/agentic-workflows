# Review: naming of `rules/` and `workflows/` — why five names collide, and how to fix it

Date: 2026-09-16. Scope: the 14 files in `rules/` and 38 in `workflows/`.

## 1. The collision

Five basenames exist in both directories:

| Basename | `rules/` (words) | `workflows/` (words) |
|---|---|---|
| `phase-discovery` | 479 | 1 989 |
| `phase-execution` | 255 | 724 |
| `phase-validation` | 217 | 653 |
| `phase-atomic-execution` | 644 | 682 |
| `phase-atomic-validation` | 289 | 663 |

## 2. What each side actually contains

**`workflows/phase-*.md`** — *orchestrators*. An `Invocation:` line, a Guard, and a
numbered sequence that calls children (`pd-analyze → pd-decompose → …`). They are what
the user types (`/phase-discovery <spec>`).

**`rules/phase-*.md`** — *context bootstrap for that phase*. Each has:
- `trigger: model_decision` (not always-on — the only rules besides `workflow-reference`
  that are model-decision);
- `## Context Bootstrap` — the ordered list of `.ai/` files to load and what to extract
  from each (`WORK_DIR`/`AI_DIR` resolution for the atomic ones);
- `## Phase Behaviors` — 4–8 bullets of phase-specific conduct;
- one has extra content: `phase-atomic-execution` carries the whole **Blocker
  Reconciliation** procedure (≈350 of its 644 words); `phase-discovery` carries
  `## Codebase Reading Rules` and `## Decision Protocol` (autonomous vs step-by-step).

So the two files with the same name are not variants of one thing. The workflow is
*what to do*; the rule is *what to load before doing it, and how to behave while doing
it*. Twenty workflow lines cite the rule side as `` follow `phase-discovery` rules — ## Context Bootstrap ``.

## 3. Why the names collide — the history

1. Windsurf has two directories, `global_workflows/` and `global_rules/`, addressed by
   bare basename. The author named the bootstrap rule after the phase it serves, and in
   Windsurf that is unambiguous: `/phase-discovery` is a workflow, "the
   `phase-discovery` rule" is a rule. Same name, different namespaces.
2. Claude Code and Codex have one namespace — skills. The 2026-07 audit (finding B-3)
   found the five rule files were never deployed there at all; the fix deployed every
   rule as `rule-<name>` (ADR-0003). The prefix exists *only* to work around this
   collision, and `workflow-globals` spends a paragraph explaining how to resolve a rule
   reference per harness.

The collision is therefore an artefact of Windsurf's namespaces leaking into the file
names, patched at deploy time rather than at the source.

## 4. What the collision costs today

- **Ambiguous citations.** `workflows/phase-pipeline.md:185` says "Read and follow
  `phase-execution.md` inline" — with the `.md` suffix, which file is meant is a guess
  (it is the workflow, but the rule is equally plausible).
- **A prose resolution rule** in `workflow-globals` that every reader must know
  ("resolve to `rule-<name>` on Claude Code and Codex, bare basename on Windsurf").
- **A contract check** in `validate-contracts.sh` that exists only to verify that the
  prefix is applied.
- **Reader confusion**: a newcomer opening `rules/phase-execution.md` expects "the rules
  of the execution phase" and finds a load list.

## 5. Wider naming review

The collision is the sharpest symptom of a broader inconsistency: file names do not
encode the file's *kind*.

### `rules/` — four naming styles in 14 files

| Style | Files | Problem |
|---|---|---|
| Subject noun | `tdd`, `git-flow`, `orchestration`, `language`, `quick-flow`, `run-log` | good — says what is governed |
| Scope label | `workflow-globals`, `workflow-reference` | "globals" and "reference" say where the text sits, not what it is; `workflow-reference` is 4 260 words of *five* different things (file responsibilities, protected sections, decision protocol, subtask classifier, decomposition rules) |
| Deployment target | `global-claude` | named after where it is copied (`~/.claude/CLAUDE.md`), not what it contains (the always-on essentials); its Codex twin lives in `templates/codex-global-AGENTS.md` — a different directory for the same kind of file |
| Phase name | `phase-*` (5) | the collision above; content is a *bootstrap*, not a rule set |

### `workflows/` — prefixes that must be decoded

| Prefix | Meaning | Count |
|---|---|---|
| `phase-` | orchestrator (also used by the reference doc's sibling `phase-pipeline`) | 7 |
| `pd-` / `pe-` / `pv-` | Discovery / Execution / Validation child step | 6 / 2 / 7 |
| `pae-` / `pav-` | Atomic execution / atomic validation child step | 3 / 3 |
| none | entry points and utilities (`spec-run`, `bugfix`, `retro`, `compress-state`, `suggest-*`, …) | 12 |
| `PIPELINE.md` | reference document, upper-case, **not executable — yet deployed as a skill by `sync.sh`** | 1 |

`pd`/`pe`/`pv`/`pae`/`pav` are internally consistent but opaque: nothing in `pav-close`
says "validation" to someone who has not read the legend. Step order is not in the
name either — `pd-design` is step 3 and `pd-decompose` step 2, alphabetically reversed.

## 6. Recommendations

Ordered by impact; R1–R3 remove the collision, R4–R6 make the rest self-describing.
All are renames plus reference updates — `validate-contracts.sh` will catch every
missed citation, which is exactly what it is for.

### R1 — Rename the five bootstrap rules by their kind: `bootstrap-<phase>`
`rules/phase-discovery.md` → `rules/bootstrap-discovery.md`, and likewise
`bootstrap-execution`, `bootstrap-validation`, `bootstrap-atomic-execution`,
`bootstrap-atomic-validation`. The word says what the file does (load context) and the
suffix says for whom. Citations become `` follow `bootstrap-discovery` → ## Context Bootstrap ``
— unambiguous in every harness, no `.md`-suffix guessing.

Consequences: the `rule-` deploy prefix is no longer *required* for correctness (keep it
as a namespace convention or drop it — see R4); the resolution paragraph in
`workflow-globals` shrinks to one line; one check group in `validate-contracts.sh`
becomes a plain "file exists" check.

### R2 — Move the two non-bootstrap procedures out of the bootstrap files
- Blocker Reconciliation (`rules/phase-atomic-execution.md`) → its own rule
  `rules/blocker-reconciliation.md` (it is a procedure with its own trigger, cited from
  two workflows).
- `## Decision Protocol` and `## Codebase Reading Rules` (`rules/phase-discovery.md`) →
  `rules/discovery-conduct.md`, or fold Decision Protocol into `workflow-reference`'s
  Autonomous Decision Protocol section, which already owns the canonical definition.

After R2 every `bootstrap-*` file is a load table plus behaviours, under 300 words.

### R3 — Fix the ambiguous inline citations now, independent of renames
`phase-pipeline.md:185,225`: "Read and follow `phase-execution.md` inline" → "Run the
`/phase-execution` workflow's steps inline". Add a contract check that no citation
carries a `.md` suffix for a name that exists in both directories.

### R4 — Name rules by kind, consistently: `<kind>-<subject>` or bare subject
Proposed final layout of `rules/`:

| Current | Proposed | Rationale |
|---|---|---|
| `workflow-globals` | `contract-phases` | it *is* the phase contract and canonical status formats |
| `workflow-reference` | split: `contract-state-files` (file roles, protected sections, formats), `protocol-autonomous-decision`, `protocol-subtask-classifier`, `contract-multi-phase` | one file per concept; each becomes citeable by a name that says what it is |
| `global-claude` | `always-on-claude` (and move `templates/codex-global-AGENTS.md` → `rules/always-on-codex`) | named by role, siblings side by side |
| `tdd`, `git-flow`, `orchestration`, `quick-flow`, `run-log`, `language` | keep | already subject-named |
| `phase-*` | `bootstrap-*` (R1) | |

Deploy prefix: keep `rule-` for skills so the skill list groups rules together, but
state it as a convention, not a collision workaround.

### R5 — Make workflow names readable without a legend
Two viable schemes; pick one in an ADR.

**Scheme A — spell the phase, keep step order in front matter only:**
`pd-analyze` → `discovery-analyze`, `pae-tests` → `atomic-exec-tests`,
`pav-close` → `atomic-val-close`, `pv-issues` → `validation-issues`. Cost: longer slash
commands (`/discovery-decompose`). Benefit: no legend.

**Scheme B — keep the short prefixes, add a `step:` and `phase:` front-matter key
and render the legend into `docs/USAGE.md` automatically** (this is `specs/10`). Cost:
the legend stays necessary. Benefit: no command renames, nothing breaks for existing
users.

Recommendation: **Scheme B now** (zero-cost, ships with spec 10), reconsider A when the
open-source release (spec 11) sets the public command names — renaming before a public
release is free, after it is a breaking change.

### R6 — Take `PIPELINE.md` out of `workflows/`
It is documentation, deployed as a skill only because it sits in the directory
`sync.sh` copies. Move it to `docs/PIPELINE.md`, update the six citations, and add a
contract check that every file in `workflows/` has an `Invocation:` line.

## 7. Suggested execution

One spec: `.ai/specs/13-rules-workflows-naming.md` covering R1–R4 and R6 (R5 is folded
into spec 10/11). Order inside the task: R3 (pure fix) → R6 → R1 → R2 → R4. Each rename is
`git mv` + `sed` over `workflows/ rules/ docs/ templates/ *.sh` + `validate-contracts.sh`
green + `sync.sh`. Requires spec 01 (git) first — a rename sweep without version control
is not reviewable.
