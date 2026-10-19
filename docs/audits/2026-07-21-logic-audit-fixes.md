# Logic Audit Fixes — agentic_workflows

Source: independent logic audit, 2026-07-21 — 4 BLOCKER, 9 MAJOR, 7 MINOR findings.
All 20 findings were re-verified against file contents before this spec was written.

## Goal

The workflow system in `agentic_workflows` contains four defects that make a normal run
hit a dead end (`/pd-archive` unreachable, composite `## Subtask Progress` blocks never
created, phase rule files never deployed to Claude Code / Codex projects, composite
integration validation triggered twice), nine defects that produce wrong or missing
state (broken rule references, `/phase-execution` ↔ `/phase-validation` deadlock,
multi-phase naming bypassed by `/phase-pipeline`, four unhandled blocking points in the
"fully autonomous" pipeline, silently compressed improvement proposals, failed
validations invisible in `plan.md`, inconsistent `--batch` semantics, an unreachable
template reference, a corrupt ADR index schema), and seven inconsistencies that degrade
reliability.

The goal is to apply all 20 fixes in a conflict-free order, so that: a Discovery →
Execution → Validation run completes end-to-end for flat, composite (Type 2) and
re-sliced (Type 3) tasks; `/phase-pipeline` runs without an unplanned stop; every
cross-file reference resolves to a section that exists; and `validate-contracts.sh`
gains three new check groups that would have caught the defect classes M-5, B-3 and
F-18.1 before a sync.

## Acceptance Criteria

### Blockers

- [ ] `pd-finalize` sets `discovery: complete` **before** invoking `/pd-archive`; a full
      `/phase-discovery` run on a fresh spec produces `state-archive.md` in the task
      directory without any user prompt (B-1)
- [ ] `pd-decompose` writes a `## Subtask Progress` section to the task-level `state.md`
      with one block per created subtask — leaf blocks for leaves, `[composite]` blocks
      for Type 2 composites, including `children:` (B-2)
- [ ] Re-running `/pd-decompose` on an existing task upserts `## Subtask Progress`
      blocks by ID: no duplicate blocks, and no block whose status is beyond
      `not-started` is reset (B-2)
- [ ] `pe-execute` step 1 reads the authoritative children list from
      `T-XX/description.md → ## Context → children:`, not from `state.md`; a missing
      composite block no longer stops execution (B-2)
- [ ] `setup-new-project.sh` copies all eight rule files
      (`workflow-globals`, `workflow-reference`, `language`, and the five `phase-*`)
      into both `.windsurf/rules/` and `.devin/rules/` (B-3)
- [ ] `sync.sh` deploys every `rules/*.md` as `~/.claude/skills/rule-<name>/SKILL.md`
      and `~/.codex/skills/rule-<name>/SKILL.md` (B-3)
- [ ] **All four agents resolve all eight rule files.** After `setup-new-project.sh` +
      `sync.sh`, each of Claude Code, Codex, Windsurf and Devin has a reachable copy of
      every file in `rules/` — verified against the deployment matrix in CHANGE 1 (B-3)
- [ ] Deploying rules as skills does not overwrite any workflow skill: the five
      colliding basenames (`phase-discovery`, `phase-execution`, `phase-validation`,
      `phase-atomic-execution`, `phase-atomic-validation`) exist twice under
      `~/.claude/skills/` and `~/.codex/skills/` — once bare (workflow), once
      `rule-`-prefixed (rule) — with distinct contents (B-3)
- [ ] `workflow-globals` Context Bootstrap table names the Claude Code / Codex skill
      (`rule-phase-discovery`, …) alongside the Windsurf / Devin rule name, so the
      reference cannot be confused with the identically-named workflow (B-3)
- [ ] `/phase-composite-validation` is triggered exactly once per composite — by
      `pav-close` when the last child closes; `pe-execute` only verifies the outcome and
      records `composite-stalled` when it is still `not-started` (B-4)

### Majors

- [ ] Zero occurrences of `workflow-globals → ## Decomposition Rules`,
      `workflow-globals → ## .ai/memory/state.md Entry Format`,
      `workflow-globals → ## .ai/project_state.md Update Rules`, and
      `Status Translation Table in workflow-globals` remain in `workflows/` (M-5)
- [ ] `/phase-execution` on a task where every subtask is `done`/`reviewed` and
      `execution` is not `complete` calls `/pe-finalize` instead of suggesting
      `/phase-validation`; the deadlock with `/phase-validation` Step 0 is gone (M-6)
- [ ] `/phase-pipeline` on a multi-phase spec creates `task-<basename>-p<N>/` and writes
      `active_phase:`, `spec_phase_count:` and `## Spec Phases` — identical to
      `/phase-discovery` on the same spec (M-7)
- [ ] `## Pipeline Overrides` covers all four remaining blocking points
      (`pe-finalize` step 5, `pav-check` NEEDS WORK, `phase-composite-validation`
      NEEDS WORK, `pv-contract` critical-failure gate), each mapped to a recorded
      artifact (M-8)
- [ ] The `pav-check` pipeline override escalates to the user when the same subtask
      fails validation twice (M-8)
- [ ] `## Improvement Proposals (T-XX)` is listed in the Protected Sections Contract;
      `/compress-state --auto` invoked by `pav-close` no longer removes it (M-9)
- [ ] On a NEEDS WORK verdict, `pav-check` sets the T-XX row `Status` in parent
      `plan.md` to `blocked`; `pe-execute` no longer treats it as a satisfied
      dependency (M-10)
- [ ] `pv-execute-fixes` passes `--batch` to `/phase-atomic-validation`, matching
      `pe-execute` (M-11)
- [ ] `pav-propose` defines a third mode `--batch --apply`; `phase-pipeline` Phase 2 and
      Phase 3 override rows describe passing that flag rather than behaviour the flag
      does not have (M-11)
- [ ] `pe-finalize` step 5 no longer references the non-existent flag
      `/pe-execute --batch` (M-11)
- [ ] `pv-create-fixes` step 3 points at the in-repo five-section template in
      `pd-decompose` step 3; no reference to `templates/subtask-description.md`
      remains in `workflows/` (M-12)
- [ ] `pv-finalize` step 3.7 appends rows matching the existing
      `| Number | Title | Status | Date | Link |` header under `## Records`, and only
      creates that same header when the file has no table (M-13)

### Minors

- [ ] `workflow-reference → ## File Responsibility` documents `description.md` with five
      sections including `## Scope` (F-14)
- [ ] `pv-finalize` step 3.3 derives `<ID>` from the task directory numeric prefix, with
      `spec_path:` prefix as fallback and `unknown` only as last resort (F-15)
- [ ] `pd-finalize` step 1 accepts all four `plan.md` schemas emitted by `pd-decompose`
      (flat, +`Repo`, +`Type`, +`Type`+`Slice`+`Repo`) and requires
      `## Decomposition Decisions` when `Type` or `Slice` is present (F-16)
- [ ] `pd-analyze` uses `### Open Questions` and `### Codebase Analysis` (three hashes)
      in all three prose references, matching its own template (F-17)
- [ ] `onboard-legacy-project` contains no reference to the non-existent
      `/codebase-audit`; its progress template tracks Phase 2 per file (12 checkboxes)
      and Phase 0.2 resumes from the first unticked file (F-18)
- [ ] `pd-finalize` step 3b checks for `state-archive.md` before invoking `/pd-archive`
      and skips the invocation when it exists; a resumed Discovery run never stops for
      the archive confirmation (F-19)
- [ ] `phase-discovery` step 4b.d searches for `task-<basename>-p<N>/` under all of
      `.ai/tasks/`, not just `todo/` (F-20)

### Contract validation

- [ ] `validate-contracts.sh` fails when any `` `workflow-globals → ## <section>` ``
      reference in `workflows/` names a section absent from `rules/workflow-globals.md`
- [ ] `validate-contracts.sh` fails when a rules file named in the `workflow-globals`
      Context Bootstrap table is missing from the `setup-new-project.sh` copy list
- [ ] `validate-contracts.sh` fails when a `` `/command` `` referenced in `workflows/`
      has no matching `workflows/<command>.md`
- [ ] `bash validate-contracts.sh` exits 0 after all changes are applied

---

## Implementation Plan

Changes are numbered in application order. Steps 1–9 are order-sensitive (three pairs
touch the same region); steps 10–20 are mutually independent; step 21 runs last.

---

### CHANGE 1 (B-3) — deploy phase rule files to every agent

**Current state.** `setup-new-project.sh` copies three rules (`workflow-globals.md`,
`workflow-reference.md`, `language.md`) into `.windsurf/rules/` (loop at line 84) and
`.devin/rules/` (loop at line 117). `sync.sh` deploys all `rules/*.md` to
`~/.codeium/windsurf/global_rules/` (step 2) and the full eight-file list into
per-project `.devin/rules/` and `.windsurf/rules/` (step 5b) — but only for projects
that already contain `.devin/`. For Claude Code and Codex, no rules file is deployed
anywhere: `~/.claude/skills/` and `~/.codex/skills/` receive only `workflows/*.md` and
`principles/*.md`.

**Deployment matrix — target state.** The fix is agent-complete, not Claude-Code-only.
Each cell must hold all eight rule files after `sync.sh` (global) and
`setup-new-project.sh` (per project):

| Agent | Global path | Per-project path | Current gap | Fixed by |
|---|---|---|---|---|
| Claude Code | `~/.claude/skills/rule-<name>/SKILL.md` | symlinked from global by step 5b | **total — no rules anywhere** | 1b |
| Codex | `~/.codex/skills/rule-<name>/SKILL.md` | `AGENTS.md` only (no rules) | **total — no rules anywhere** | 1c |
| Windsurf | `~/.codeium/windsurf/global_rules/<name>.md` | `.windsurf/rules/<name>.md` | 5 phase rules missing at setup time | 1a |
| Devin | `~/.codeium/windsurf/global_rules/<name>.md` | `.devin/rules/<name>.md` | 5 phase rules missing at setup time | 1a |

Windsurf and Devin already receive all eight files globally (`sync.sh` step 2 copies
`"$RULES"/*.md` unfiltered) and per-project on any later sync pass (step 5b). Their gap
is narrower — a project set up but not yet synced — and 1a closes it. Claude Code and
Codex have no path at all, which is what 1b and 1c add.

**1a.** In `setup-new-project.sh`, replace the rule list in both loops (`.windsurf/rules/`
at line 84, `.devin/rules/` at line 117) with the eight-file list already used by
`sync.sh:128-130`:

```bash
for rule in workflow-globals.md workflow-reference.md language.md \
            phase-discovery.md phase-execution.md phase-validation.md \
            phase-atomic-execution.md phase-atomic-validation.md; do
```

Keep the existing per-file `if [ ! -f … ]` / `WARNING … not found` behaviour unchanged —
idempotency and the "already present" message must survive.

**1b.** In `sync.sh`, add step `3c` immediately after step `3b` (Claude Code principles,
line 62), mirroring the `principle-*` pattern:

```bash
# ── 3c. Claude Code: rules as skills ──────────────────────────────────
echo "[3c/5] Claude Code: rules as skills"
for file in "$RULES"/*.md; do
  name=$(basename "$file" .md)
  skill_name="rule-${name}"
  mkdir -p ~/.claude/skills/$skill_name
  cp "$file" ~/.claude/skills/$skill_name/SKILL.md
  echo "  deployed: $skill_name"
done
```

**1c.** In `sync.sh`, add the same block for Codex as step `4d`, after step `4c`
(global AGENTS.md), writing to `~/.codex/skills/rule-${name}/SKILL.md`.

**Why the `rule-` prefix is mandatory.** Five basenames exist in *both* `workflows/` and
`rules/`: `phase-discovery.md`, `phase-execution.md`, `phase-validation.md`,
`phase-atomic-execution.md`, `phase-atomic-validation.md`. Deploying rules under their
bare names into `~/.claude/skills/` would overwrite the workflow skills of the same
name. The prefix is a correctness requirement, not a style choice.

**1d.** In `rules/workflow-globals.md`, extend the Context Bootstrap table (lines 11–17)
with a third column so the prefixed name is discoverable:

| Phase | Rules file (Windsurf / Devin) | Skill name (Claude Code / Codex) | Loaded by |
|-------|------------------------------|----------------------------------|-----------|
| Discovery | `phase-discovery` | `rule-phase-discovery` | `/phase-discovery`, `/pd-analyze` |
| Execution | `phase-execution` | `rule-phase-execution` | `/phase-execution`, `/pe-execute` |
| Validation | `phase-validation` | `rule-phase-validation` | `/phase-validation`, `/pv-contract`, `/pv-review` |
| Atomic Execution | `phase-atomic-execution` | `rule-phase-atomic-execution` | `/phase-atomic-execution`, `/pae-implement` |
| Atomic Validation | `phase-atomic-validation` | `rule-phase-atomic-validation` | `/phase-atomic-validation`, `/pav-check` |

Add one line below the table:

> On Claude Code and Codex, rules are deployed as skills under the `rule-` prefix
> (`workflow-globals` → `rule-workflow-globals`). The prefix avoids a name collision
> with the identically-named phase *workflows*. Resolve a rules reference to the
> `rule-`-prefixed skill on those agents, and to the bare filename in
> `.windsurf/rules/` or `.devin/rules/` on Windsurf and Devin.

**1e.** In `sync.sh`, add the two new destinations to the `Deployed to:` summary block.

**Verification.** `bash sync.sh` then confirm
`~/.claude/skills/rule-phase-atomic-execution/SKILL.md` and
`~/.codex/skills/rule-workflow-reference/SKILL.md` exist, and that
`~/.claude/skills/phase-atomic-execution/SKILL.md` still holds the *workflow* (not the
rule).

---

### CHANGE 2 (M-5) — retarget ten references from `workflow-globals` to `workflow-reference`

`rules/workflow-globals.md` has exactly three `##` sections: `## Canonical Status
Formats` (line 55), `## Phases` (61), `## Fix-Tasks` (115). The four referenced sections
live in `rules/workflow-reference.md`: `## Status Translation Table` (129),
`## .ai/memory/state.md Entry Format` (213), `## .ai/project_state.md Update Rules`
(236), `## Decomposition Rules` (375).

Substitute `workflow-globals` → `workflow-reference` at exactly these ten sites, leaving
surrounding wording untouched:

| # | File | Line | Current fragment |
|---|------|------|------------------|
| 1 | `workflows/pd-decompose.md` | 36 | `` following the `## Decomposition Rules` in `workflow-globals` `` |
| 2 | `workflows/pd-decompose.md` | 40 | `per workflow-globals → ## Decomposition Rules` |
| 3 | `workflows/pav-close.md` | 39 | `per Status Translation Table in workflow-globals` |
| 4 | `workflows/pae-finalize.md` | 59 | `per Status Translation Table in workflow-globals` |
| 5 | `workflows/pd-finalize.md` | 60 | `` `workflow-globals → ## .ai/memory/state.md Entry Format` `` |
| 6 | `workflows/pd-finalize.md` | 72 | `` `workflow-globals → ## .ai/project_state.md Update Rules` `` |
| 7 | `workflows/pe-finalize.md` | 54 | `` `workflow-globals → ## .ai/memory/state.md Entry Format` `` |
| 8 | `workflows/pe-finalize.md` | 57 | `` `workflow-globals → ## .ai/project_state.md Update Rules` `` |
| 9 | `workflows/pv-finalize.md` | 47 | `` `workflow-globals → ## .ai/memory/state.md Entry Format` `` |
| 10 | `workflows/pv-finalize.md` | 51 | `` `workflow-globals → ## .ai/project_state.md Update Rules` `` |

**Do not touch** the five legitimate `workflow-globals` references that point at rules
which really do live there: `PIPELINE.md:9`, `phase-pipeline.md:13`,
`phase-pipeline.md:52`, `phase-discovery.md:42`, `phase-discovery.md:49-50`.

---

### CHANGE 3 (B-1) — move the phase flip before the archive call in `pd-finalize`

**Current state.** `workflows/pd-finalize.md` step 3b (line 53) invokes `/pd-archive`;
step 6 (line 85) sets `discovery: complete`. `pd-archive` Guard step 2 (line 16) stops
unless `discovery: complete`, so the archive never runs.

Renumber the `## Instructions` steps of `pd-finalize` as follows:

| New | Old | Content |
|-----|-----|---------|
| 1 | 1 | consistency review (unchanged; further amended by CHANGE 17) |
| 2 | 2 | per-subtask verification (unchanged) |
| 3 | 3 | `/compress-state --auto` (unchanged) |
| **3a** | **6** | Update `## Phases` in `state.md`: set `discovery: complete`. |
| 3b | 3b | `/pd-archive` invocation (amended by CHANGE 4) |
| 4 | 4 | state-file updates (unchanged) |
| 5 | 5 | root-file updates (unchanged) |
| 6 | 7 | final report (unchanged) |

New step 3a text:

> 3a. Update `## Phases` in `state.md`: set `discovery: complete`.
>     This must happen before step 3b — `/pd-archive` guards on this flag.

Delete old step 6. Leave `pd-archive`'s Guard step 2 unchanged: it remains valid
protection against manual invocation before Discovery finishes.

**Safety.** Steps 4 and 5 do not read `## Phases`, so the earlier flip cannot change
their behaviour. `pd-finalize`'s own Guard (line 20) reads `## Phases` before any of
this and is unaffected.

---

### CHANGE 4 (F-19) — make `pd-finalize` honour its own "skip without error" contract

Applies on top of the step 3b produced by CHANGE 3. Replace lines 53–56 with:

> 3b. Archive verbose Discovery content to reduce Execution-phase context load:
>     - If `state-archive.md` already exists in the task directory (resume case) →
>       do **not** invoke `/pd-archive`. Report:
>       "state-archive.md already present — archive skipped." Continue to step 4.
>     - Otherwise → run `/pd-archive <task-directory>`.

`pd-archive` Guard step 3 stays unchanged — it protects manual invocation. The caller
now never reaches it, so an autonomous Discovery re-run cannot stop for a confirmation
that `phase-discovery.md:61-63` forbids overriding.

---

### CHANGE 5 (B-2) — initialise `## Subtask Progress` in `pd-decompose`

**Current state.** `rules/workflow-globals.md:80` declares that the `[composite]` block
is "written by `pd-decompose`". `pd-decompose`'s only state-file write is step 5, which
appends `## Decomposition` (`decomposition:`, `subtasks:`, `composites:`,
`sliced-pairs:`). No `## Subtask Progress` section is ever created before execution
begins. The only writer of a `[composite]` block anywhere is the runtime tripwire
(Composite Promotion Protocol, `rules/workflow-reference.md:357`).

**5a.** Insert a new step 5a into `workflows/pd-decompose.md`, between step 5
(`## Decomposition` marker) and step 6 (completion report):

> 5a. **Initialise `## Subtask Progress` in the task-level `state.md`.** Write one block
>     per subtask created in step 3, using the formats in
>     `workflow-reference → ## Parent state.md — ## Subtask Progress Format`:
>
>     - **Leaf subtasks** — leaf block with `atomic-execution: not-started`,
>       `atomic-validation: not-started`, `last_action:` empty, `target_files:` empty,
>       `blocker: none`, `notes:` empty. All five fields are written even when empty —
>       they are protected fields (`workflow-reference → ## Protected Sections Contract`).
>     - **Type 2 composites** — `[composite]` block with `rollup: not-started`,
>       `integration-validation: not-started`, `children:` listing every child ID in
>       execution order, `blocker: none`, `notes:` the classifier rationale (which
>       signals fired, recorded in `plan.md → ## Decomposition Decisions`).
>     - **Type 3 re-sliced subtasks** — all leaves; write leaf blocks only. Type 3
>       produces no composite rows.
>
>     **Upsert semantics.** If `## Subtask Progress` already exists (re-run after Guard
>     confirmation), match blocks by T-XX ID: create missing blocks, leave existing
>     blocks untouched. Never duplicate a block, and never reset a block whose
>     `atomic-execution` or `atomic-validation` status is beyond `not-started`. A leaf
>     block that the Composite Promotion Protocol has already converted to `[composite]`
>     for the same ID is left as-is.

**5b.** Make the reader side defensive. In `workflows/pe-execute.md:38`, replace:

> - Verify all child rows (listed in `children:` of the composite block in
>   `state.md → ## Subtask Progress`) are present in `plan.md`. If any child row is
>   missing → **stop**: "Composite T-XX children mismatch. Re-run `/pd-decompose` to
>   regenerate."

with:

> - Read the authoritative children list from `T-XX/description.md → ## Context →
>   `children:`` (written by `pd-decompose` step 3). Verify every listed child has a row
>   in `plan.md`. If any child row is missing → **stop**: "Composite T-XX children
>   mismatch between description.md and plan.md. Re-run `/pd-decompose` to regenerate."
> - Use the `[composite]` block in `state.md → ## Subtask Progress` for *status only*.
>   If the block is absent, create it with `rollup: not-started`,
>   `integration-validation: not-started`, `children:` from `description.md`,
>   `blocker: none`, and continue — a missing block is a recoverable state, not a stop.

**Non-conflict.** This makes `workflow-globals:80` true rather than aspirational, so no
rule text changes. The upsert clause keeps it compatible with the Composite Promotion
Protocol.

---

### CHANGE 6 (B-4) — single owner for the composite integration-validation trigger

Depends on CHANGE 5. `workflows/pe-execute.md` currently instructs the trigger twice:
step 1 bullet 4 (line 40) calls `/phase-composite-validation` directly, while step 2e
(line 49) states that `pav-close` already did it. `pav-close` step 5c (lines 52–55) does
perform the call, so the second invocation hits
`phase-composite-validation` Step 0.3 (`integration-validation: complete` → "Confirm?
(yes/no)"), halting an unattended batch loop.

Replace the step 1 bullet at `pe-execute.md:40` with:

> - After all children reach `reviewed`, do **not** call
>   `/phase-composite-validation` — `pav-close` triggers it when the last child closes
>   (see step 2e). Only verify afterwards that the composite block shows
>   `integration-validation: complete` or `failed`. If it is still `not-started`, record
>   the composite as `composite-stalled` in the `## Execution Report` and continue with
>   the remaining rows.

`pav-close` and `phase-composite-validation` are not edited. The `composite-stalled`
vocabulary already exists (`PIPELINE.md:223`) and `pe-finalize` step 2b already knows how
to report it.

---

### CHANGE 7 (M-11) — settle `--batch` semantics across the three callers

Three inconsistencies around the same flag:

1. `pe-execute.md:48` passes `--batch` to `/phase-atomic-validation`;
   `pv-execute-fixes.md:30` does not — identical atomic cycles behave differently.
2. `phase-pipeline.md:136` says "`pav-propose` 'Do Now' items → apply automatically",
   but `pav-propose --batch` is defined (line 10 and step 4) as "do NOT prompt and do
   NOT apply".
3. `pe-finalize.md:74` attributes deferred proposals to `/pe-execute --batch` — a flag
   `pe-execute` does not accept.

**7a.** In `workflows/pv-execute-fixes.md` step 3b (line 30), change to:

> b. Call `/phase-atomic-validation <path-to-fix-task/description.md> --batch`

**7b.** In `workflows/pav-propose.md`, add a third bullet to `**Modes:**` (after line 10):

> - **Batch-apply** (`--batch --apply`): record all proposals to `state.md` *and* apply
>   the `Do Now` items without prompting. `Do Later` / `Optional` are recorded only.
>   Used by `/phase-pipeline`.

And extend step 4 with a third branch:

> - **Batch-apply mode** (`--batch --apply`): do NOT prompt. Apply every `Do Now` item,
>   then record all proposals to `state.md`, listing the applied items under a
>   `### Applied (pipeline)` heading inside `## Improvement Proposals (T-XX)`. Print:
>   "Batch-apply mode: N Do Now proposal(s) applied for T-XX."

**7c.** In `workflows/pav-propose.md` step 5, add `### Applied (pipeline)` to the section
skeleton as an optional fourth subsection (written only in batch-apply mode).

**7d.** In `workflows/phase-pipeline.md`, replace the Phase 2 override bullet (line 136)
with:

> - `pav-propose` "Do Now" items → applied automatically: `/phase-atomic-validation` is
>   invoked with `--batch --apply`, which passes both flags through to `pav-propose`.
>   `Do Later` / `Optional` → recorded in `state.md`, skipped.

Add the identical bullet to the Phase 3 (Validation) override list, covering the
`pv-execute-fixes` loop.

**7e.** In `workflows/pe-finalize.md:74`, replace "batch proposals collected during
`/pe-execute --batch`" with "batch proposals collected during the batch atomic
validation cycles run by `/pe-execute`".

**7f.** In `rules/workflow-globals.md:37`, update the autonomous-mode table row for
`/pav-propose` to name both flag forms: `` `--batch` or `--batch --apply` passed ``.

---

### CHANGE 8 (M-8) — cover the four remaining pipeline blocking points

Depends on CHANGE 7 (`--batch --apply` must exist first). `phase-pipeline` claims a
"fully autonomous" run but its `## Pipeline Overrides` table (lines 16–21) covers only
four rules. Four other workflows stop and wait: `pe-finalize.md:74-89`,
`pav-check.md:74`, `phase-composite-validation.md:88-90`, `pv-contract.md:65-69`.

Append four rows to the `## Pipeline Overrides` table:

| Overridden rule | Pipeline behavior |
|---|---|
| `pe-finalize` step 5 — wait for Do Now choice | Auto-select option 2 (apply inline now). Record the applied list in `state.md → ## Improvement Proposals (T-XX)` under `### Applied (pipeline)`. In practice this is a no-op once CHANGE 7 is applied, because `--batch --apply` leaves no deferred Do Now items; the row remains as a safety net for proposals written by a non-pipeline session. |
| `pav-check` NEEDS WORK — stop and surface findings | Record the verdict and the `plan.md` `blocked` status (CHANGE 12), then create a fix-task for the failing subtask using the `pv-create-fixes` Case A / Case B naming rules and continue the loop. **Escalate to the user if the same T-XX fails validation twice** — track the count in the T-XX `notes:` field as `pipeline-fix-attempts: N`. |
| `phase-composite-validation` NEEDS WORK — wait for fix approval | Auto-approve every `critical` and `important` integration finding; create the D8 fix sibling per Step 2.3; defer `optional` findings to `state.md`. |
| `pv-contract` critical-failure gate | Auto-select `continue-marked`; write `### Critical Failures Decision: continue-marked` to `state.md` so `pv-review`'s Guard step 4 passes and each failure is carried into `### Findings` as a `critical` item. |

The twice-fails escalation clause is required: without it, an unconditional auto-fix
introduces an infinite fix → fail → fix loop.

None of the four target workflows is edited — their standalone and `/phase-validation`
behaviour is unchanged.

---

### CHANGE 9 (M-9) — protect `## Improvement Proposals` from compression

`pav-propose` step 5 writes `## Improvement Proposals (T-XX)` to the task-level
`state.md`; `pav-close` step 4 immediately runs `/compress-state --auto` on that same
file. The Protected Sections Contract (`rules/workflow-reference.md:151-169`) does not
list the section, and `compress-state` classifies closed-out content as `[STALE]` and
intermediate reasoning as `[VERBOSE]`. `--auto` skips confirmation, so the loss is
silent — and `pe-finalize` step 5, whose only job is to consume those sections, finds
nothing.

In `rules/workflow-reference.md`, add one line to the **Task-level `state.md`** list of
`## Protected Sections Contract`, after `## Subtask Progress`:

> - `## Improvement Proposals (T-XX)` (one per subtask — consumed by `/pe-finalize`
>   step 5; removable only by that step, and only the `### Do Now` subsection. The
>   `### Applied (pipeline)` subsection is a permanent record — never remove.)

`pe-finalize` step 5 option 3 already scopes its own removal correctly ("remove only the
'Do Now' subsections […]; preserve 'Do Later' / 'Optional' entries") — no change needed
there.

---

### CHANGE 10 (M-6) — break the `/phase-execution` ↔ `/phase-validation` deadlock

`workflows/phase-execution.md:48` currently reads:

> If no pending subtasks → suggest `/phase-validation`. **Stop.**

This branch is reached after a session is interrupted between the last `pav-close` and
`pe-finalize`: `execution: in-progress`, all subtasks `done`/`reviewed`. It stops before
the `## Execution` section, so `/pe-finalize` — the only writer of `execution: complete`
(`pe-finalize.md:47`) — never runs, and `/phase-validation` Step 0 bounces the user back
with "Execution not complete."

Replace with:

> If no pending subtasks remain:
> - and `execution` is **not** `complete` → skip `/pe-execute` and call
>   `/pe-finalize <task-directory>` to close the phase. Then report the phase summary and
>   **stop**.
> - and `execution` is already `complete` → report "Execution already complete." and
>   suggest `/phase-validation`. **Stop.**

`pe-finalize`'s own Guard already handles the `execution: complete` case, so the new
call is idempotent.

---

### CHANGE 11 (M-7) — delegate task-directory derivation in `/phase-pipeline`

`phase-pipeline.md:59-63` derives `task_dir = .ai/tasks/todo/task-` + basename(arg,
".md"), duplicating a rule that `phase-discovery` Step 4b (lines 123–139) has since
extended: multi-phase specs use `task-<basename>-p<N>/` and additionally write
`active_phase:`, `spec_phase_count:` and `## Spec Phases`. Running `/phase-pipeline` on a
multi-phase spec therefore produces the single-phase directory with no phase fields, and
`pd-analyze` step 1e — finding no `active_phase:` — treats the entire spec as the task
statement, defeating the multi-phase design.

Replace Step 0.2a with:

> a. If the argument ends with `.md` and its path starts with `.ai/specs/` → treat as a
>    spec path (new task). Do **not** derive the task directory here. Execute
>    `phase-discovery` Steps 0.1 – 0.7 verbatim — including Step 4b multi-phase
>    detection and Step 5 prefix-uniqueness guard — and adopt the task directory that
>    procedure produces. A `--phase N` argument passed to `/phase-pipeline` is forwarded
>    to it unchanged.

Branches b (task directory) and c (legacy mode) are unchanged. This removes a duplicated
rule rather than adding a second one, keeping multi-phase naming single-sourced.

---

### CHANGE 12 (M-10) — propagate a failed validation to `plan.md`

The Status Translation Table (`rules/workflow-reference.md:136-143`) maps `failed` →
`plan.md: blocked`, but no workflow performs that write: `pae-finalize` sets `done`,
`pav-close` sets `reviewed` and is skipped on NEEDS WORK (its Pre-check stops with
"Cannot close: verdict is NEEDS WORK"), and `pav-check` writes only
`atomic-validation: failed` inside `## Subtask Progress`. `plan.md` therefore still
shows `done`, so `pe-execute` step 2b treats the row as a satisfied dependency and starts
dependent subtasks on top of a failed one.

In `workflows/pav-check.md`, immediately after the NEEDS WORK verdict recording
(line 72), add:

> On **NEEDS WORK**, also update parent `plan.md`: set this T-XX row's `Status` column to
> `blocked`, per `workflow-reference → ## Status Translation Table` (`failed` →
> `blocked`). Record the failure reason in `state.md → ## Execution Report`.
> When a later fix-task closes the finding and validation is re-run, `pav-close` step 2
> restores `Status: reviewed`.

`pav-close` step 2 sets `reviewed` unconditionally, so recovery needs no extra rule.

---

### CHANGE 13 (M-12) — remove the unreachable `subtask-description.md` reference

`workflows/pv-create-fixes.md:55` points at a template "provided by
setup-new-project.sh in the project — see .windsurf/rules/ or project root".
`setup-new-project.sh` copies `templates/subtask-description.md` nowhere; the file exists
only in `agentic_workflows/templates/`. The reference resolves to nothing, so fix-task
descriptions are improvised — while `pd-finalize` step 2 enforces a strict five-section
shape that fix-tasks must also satisfy, and `pae-implement` Pre-check step 2 hard-stops
on a missing `## Scope`.

Replace line 55 with:

> - `description.md` — following the five-section subtask template in `pd-decompose`
>   step 3: `## Goal`, `## Context`, `## Scope` (with both `In scope:` and
>   `Out of scope:`), `## Steps` (3–15 numbered items), `## Acceptance Criteria`
>   (≥2 checkable conditions). The same per-subtask checks as `pd-finalize` step 2 apply
>   to fix-tasks.

Prefer removing the external dependency over shipping another file — no script change is
needed, so this does not interact with CHANGE 1. `templates/subtask-description.md`
stays in the repo as documentation (it is listed in `docs/USAGE.md`); only the workflow
reference to it is removed.

---

### CHANGE 14 (M-13) — make `pv-finalize` an adapter for the existing ADR index schema

Two incompatible schemas exist. Templates (`templates/.ai/adr/index.md`,
`templates/.ai-umbrella/adr/index.md`) and `/onboard-legacy-project` use
`| Number | Title | Status | Date | Link |` under `## Records`. `pv-finalize` step 3.7
initialises `# Decisions Index` with `| ADR | Task | Decision | Status | Date |` and
appends `| ADR-NNNN | #<task-id> | <summary> | Accepted | YYYY-MM-DD |`.

Since `setup-new-project.sh` installs the template version, the "if empty or missing —
initialize" branch never fires, and five-column rows are appended under a header whose
columns mean different things: `Title` receives a task id, `Status` a decision summary,
`Link` a date. Every phase Context Bootstrap that reads `.ai/adr/index.md` then ingests
corrupt data.

Rewrite step 3.7 as:

> **3.7. Update `.ai/adr/index.md` (the decisions index, English only).**
> - If the file already contains a `## Records` table → append one row matching its
>   existing header:
>   `| NNNN | <ADR title> | accepted | YYYY-MM-DD | [NNNN-<short-title>.md](NNNN-<short-title>.md) |`
> - Only if the file is missing or contains no table → create it with the template
>   header under a `## Records` heading:
>   ```
>   ## Records
>   | Number | Title | Status | Date | Link |
>   |--------|-------|--------|------|------|
>   ```
>   then append the row.

Delete the `# Decisions Index` / `| ADR | Task | Decision | Status | Date |`
initialisation block entirely. This standardises on the schema three other files already
produce, so no template or onboarding change is required.

---

### CHANGE 15 (F-14) — document the five-section `description.md`

`rules/workflow-reference.md:27-42` gives the `description.md` structure as `## Goal`,
`## Context`, `## Steps`, `## Acceptance Criteria`. Every producer and consumer requires
five: `pd-decompose` step 3 emits `## Scope`, `pd-finalize` step 2.3 verifies it contains
both `In scope:` and `Out of scope:`, and `pae-implement` Pre-check step 2 hard-stops
when it is absent.

Insert `## Scope` between `## Context` and `## Steps` in that structure block:

```
## Scope
In scope: what this subtask may change.
Out of scope: what it must not touch.
Target files: expected files to be modified.
Read by `pae-implement` before any change is made — a missing `## Scope` is a hard stop.
```

---

### CHANGE 16 (F-15) — derive the ADR `<ID>` from the task directory

`workflows/pv-finalize.md:114` says "`<ID>` — task ID from `description.md`", but
`workflow-reference.md:19-21` states plainly that the task directory contains no
top-level `description.md`. Step 3 of the same workflow (lines 89–90) already uses the
correct dual-mode resolution via `spec_path:`. As written, `<ID>` almost always resolves
to `unknown`, producing filenames like `0003-task-unknown-background-jobs.md`.

Replace the `<ID>` definition with:

> - `<ID>` — the numeric prefix of the task directory:
>   `task-<NN>-<slug>` → `<NN>`; `task-<NN>-<slug>-p<K>` → `<NN>p<K>`.
>   If the directory name has no numeric prefix, fall back to the numeric prefix of the
>   spec filename resolved through `spec_path:` in `state.md`. Use `unknown` only when
>   neither is resolvable (legacy task).

---

### CHANGE 17 (F-16) — accept all four `plan.md` schemas in `pd-finalize`

`pd-finalize.md:33` requires `plan.md` to have "`## Subtasks` table with columns: `ID`,
`Name`, `Key Steps (summary)`, `Depends On`, `Status`". `pd-decompose` legitimately emits
four schemas (lines 159–222): flat; flat + `Repo` (cross-repo); + `Type` (Type 2
composites); + `Type` + `Slice` + `Repo` (Type 3). Read strictly, the check fails a valid
Type 2 or Type 3 plan; read loosely, it verifies nothing.

Replace the bullet with:

> - `plan.md` has a `## Subtasks` table containing at least the columns `ID`, `Name`,
>   `Key Steps (summary)`, `Depends On`, `Status`; plus `Repo` when any subtask declares
>   `working_dir:`; plus `Type` when any composite exists; plus `Type` and `Slice` when
>   Type 3 re-slicing was applied. When `Type` or `Slice` is present,
>   `## Decomposition Decisions` must also be present.

This matches the protected-column rules already in `workflow-reference.md:198-202`.

---

### CHANGE 18 (F-17) — fix heading-level drift in `pd-analyze`

The `## Task Analysis` template (`workflows/pd-analyze.md:115-133`) defines `### Goal`,
`### Affected Parts`, `### Codebase Analysis`, `### Open Questions`, `### Assumptions` —
all `###`. Three prose references use `##`:

| Line | Current | Change to |
|------|---------|-----------|
| 100 | `` document the gap in `## Open Questions` `` | `` `### Open Questions` `` |
| 103 | `` maintain a running count in `## Codebase Analysis` `` | `` `### Codebase Analysis` `` |
| 105 | `` In `state.md → ## Codebase Analysis` `` | `` `### Codebase Analysis` `` |

Written literally as `##`, these sections land *outside* `## Task Analysis` and are
missed by `pd-archive` step 2a, which archives only what sits under the `## Task
Analysis` header before the next `##`. `pd-design` step 1 already reads
`### Codebase Analysis`.

---

### CHANGE 19 (F-18) — `onboard-legacy-project`: dangling command and coarse resume

**19a.** `workflows/onboard-legacy-project.md:757` says "If security findings were noted
— run /codebase-audit for a full security review." No such workflow exists
(`workflows/codebase-audit.md` is absent; only the unshipped design note
`specs/codebase-audit.md` exists). Replace with:

> 2. If security findings were noted — review the Phase 1.14 findings recorded in
>    `.ai/principles/coding.md → ## Forbidden Patterns`.

**19b.** Phase 2 (line 356) instructs "After writing each file, mark its phase in
`.ai/onboarding-progress.md` so the session can resume", but the template (lines 32–44)
tracks only three phase-level checkboxes. Interrupting Phase 2 after file 7 of 12 leaves
the checkbox unticked, so a resumed run re-does all twelve — mitigated only by the
"already filled → skip" rule, which then silently skips files a previous run wrote
partially.

Extend the template with a per-file checklist:

```markdown
# Onboarding Progress

## Phases
- [ ] Phase 1 — Codebase Exploration
- [ ] Phase 2 — Write Knowledge Base Files
- [ ] Phase 3 — Quality Check

## Phase 2 — Files
- [ ] File 1 — .ai/memory/architecture.md
- [ ] File 2 — …
      (one line per file, through File 12, in the order Phase 2 writes them)

## Notes
Started: <today's date and time>
```

Change Phase 0.2 resume detection (lines 28–30) to:

> - If present → read it. Resume from the first unticked entry: if Phase 2 is started but
>   not complete, continue from the first unticked line in `## Phase 2 — Files`, not from
>   the first unticked phase.

`/onboard-legacy-project` is a standalone entry point and shares no state contract with
the pipeline workflows.

---

### CHANGE 20 (F-20) — fix the contradictory search scope in multi-phase detection

`workflows/phase-discovery.md:135-136` reads: "lowest phase number with no existing
`task-<basename>-p<N>/` directory under `.ai/tasks/todo/` (check all subdirectories, not
just `todo/`)" — the parenthetical contradicts the clause it qualifies. A completed
phase's directory moves to `.ai/tasks/completed/` (`PIPELINE.md:82-83`), so searching only
`todo/` re-selects a finished phase and silently starts a duplicate discovery.

Rewrite as:

> - Else → lowest phase number for which no `task-<basename>-p<N>/` directory exists
>   anywhere under `.ai/tasks/` — search `todo/`, `completed/`, and any other sibling
>   directories.

---

### CHANGE 21 — three new check groups in `validate-contracts.sh`

`validate-contracts.sh` has 16 groups, none covering the defect classes above. Add three
groups before the `## Summary` block, following the existing `check "<desc>" "<result>"`
standard (result is the literal string `pass`, or an error message).

**Group 17 — `workflow-globals` section references resolve.** For every
`` `workflow-globals → ## <section>` `` occurrence in `workflows/*.md`, assert the named
section exists in `rules/workflow-globals.md`. Would have caught M-5.

```bash
# ── Group 17: workflow-globals section references resolve ────────────
missing_refs=""
while IFS= read -r sec; do
  grep -Fq "## ${sec}" rules/workflow-globals.md || missing_refs="$missing_refs $sec"
done < <(grep -rhoP 'workflow-globals → ## \K[^`\n]+' workflows/*.md | sort -u)
check "All workflow-globals section references resolve" \
  "$([ -z "$missing_refs" ] && echo pass || echo "sections not in workflow-globals.md:$missing_refs")"
```

Also assert the two prose forms are gone:

```bash
check "No 'Status Translation Table in workflow-globals' references" \
  "$(grep -rq 'Status Translation Table in workflow-globals' workflows/ && echo 'stale reference — table lives in workflow-reference.md' || echo pass)"

check "No 'Decomposition Rules in workflow-globals' references" \
  "$(grep -rqE 'Decomposition Rules.{0,4} in .workflow-globals|workflow-globals → ## Decomposition Rules' workflows/ && echo 'stale reference — rules live in workflow-reference.md' || echo pass)"
```

**Group 18 — Context Bootstrap rules are deployed.** Every rules file named in the
`workflow-globals` Context Bootstrap table must appear in the `setup-new-project.sh`
copy list. Would have caught B-3.

```bash
# ── Group 18: Context Bootstrap rules are deployed ───────────────────
undeployed=""
for r in phase-discovery phase-execution phase-validation \
         phase-atomic-execution phase-atomic-validation \
         workflow-globals workflow-reference language; do
  grep -q "$r\.md" setup-new-project.sh || undeployed="$undeployed $r"
done
check "All bootstrap rules are copied by setup-new-project.sh" \
  "$([ -z "$undeployed" ] && echo pass || echo "not in setup-new-project.sh copy list:$undeployed")"

check "sync.sh deploys rules as skills for Claude Code" \
  "$(grep -Fq '~/.claude/skills/$skill_name' sync.sh && grep -Fq 'rule-${name}' sync.sh && echo pass || echo 'sync.sh does not deploy rules/ as rule-* skills for Claude Code')"

check "sync.sh deploys rules as skills for Codex" \
  "$(grep -Fq '~/.codex/skills/$skill_name' sync.sh && grep -Fq 'rule-${name}' sync.sh && echo pass || echo 'sync.sh does not deploy rules/ as rule-* skills for Codex')"

# Collision guard: the five basenames shared by workflows/ and rules/ must never be
# deployed as skills under their bare name from rules/ — that would overwrite the workflow.
collisions=""
for f in rules/*.md; do
  b=$(basename "$f")
  [ -f "workflows/$b" ] && collisions="$collisions ${b%.md}"
done
if [ -z "$collisions" ]; then
  collision_result=pass
elif grep -Fq 'rule-${name}' sync.sh; then
  collision_result=pass
else
  collision_result="colliding basenames would overwrite workflow skills, rule- prefix missing in sync.sh:$collisions"
fi
check "Colliding rule/workflow basenames are deployed under the rule- prefix" \
  "$collision_result"

check "workflow-globals documents the rule- skill-name mapping" \
  "$(grep -q 'rule-phase-discovery' rules/workflow-globals.md && echo pass || echo 'workflow-globals Context Bootstrap table lacks the Claude Code / Codex skill-name column')"
```

**Group 19 — every referenced `/command` exists.** Would have caught F-18.1.

```bash
# ── Group 19: referenced /commands exist ─────────────────────────────
dangling=""
while IFS= read -r cmd; do
  [ -f "workflows/${cmd}.md" ] || dangling="$dangling /$cmd"
done < <(grep -rhoP '(?<=`)/[a-z][a-z0-9-]+(?=`)' workflows/*.md | tr -d '/' | sort -u)
check "All referenced /commands have a workflow file" \
  "$([ -z "$dangling" ] && echo pass || echo "no workflow file for:$dangling")"
```

**Known exclusions.** The Group 19 extractor must skip `/compress-state` false negatives
(the file exists) and any command documented as external. If `docs/USAGE.md` or `PIPELINE.md`
reference commands from other tools, restrict the scan to `workflows/*.md` as written
above and add an explicit allowlist variable if a legitimate external command appears.

**Run last.** `bash validate-contracts.sh` must exit 0 before `sync.sh` is run, since
`sync.sh` step 0 gates on it.

---

## Out of Scope

- **Rewriting `templates/subtask-description.md`.** CHANGE 13 removes the dangling
  reference rather than shipping the template into projects. The file stays as
  repository documentation; making it a deployed artifact is a separate decision.
- **`specs/codebase-audit.md` → a real workflow.** CHANGE 19a removes the dangling
  `/codebase-audit` reference. Implementing the audit workflow is separate work.
- **Restructuring `rules/workflow-globals.md` vs `rules/workflow-reference.md`.** CHANGE
  2 retargets references to where sections actually live; it does not move sections
  between the two files.
- **Changing the Autonomous Decision Protocol, the Autonomous Subtask Classifier, or the
  Composite Promotion Protocol.** CHANGE 5 must stay compatible with the promotion
  protocol but does not alter it.
- **`setup-umbrella.sh`, `setup-all-repos.sh`, `link-skills.sh`.** No finding touches
  them.
- **Migrating existing projects' `.ai/adr/index.md`.** CHANGE 14 makes `pv-finalize`
  adapt to whichever schema is on disk; repairing indexes already corrupted by the
  five-column append is a separate data-repair task.
- **Updating `docs/USAGE.md`.** It describes `templates/subtask-description.md` as deployed;
  reconciling the documentation is worthwhile but is not required for any acceptance
  criterion above.

## Notes

### Application order

Steps 1–9 are order-sensitive. Three pairs touch the same region:

| Step | Change | Reason for position |
|------|--------|---------------------|
| 1 | CHANGE 1 (B-3) | Every reference fix assumes the rule files are reachable. Script-level, no contract impact. |
| 2 | CHANGE 2 (M-5) | Depends on step 1. Pure text substitution. |
| 3 | CHANGE 3 (B-1) | Must precede step 4 — both edit `pd-finalize` step 3b. |
| 4 | CHANGE 4 (F-19) | Applies on top of the reordered step 3b. |
| 5 | CHANGE 5 (B-2) | Prerequisite for step 6: the composite block must exist before its trigger logic is corrected. |
| 6 | CHANGE 6 (B-4) | Depends on step 5. |
| 7 | CHANGE 7 (M-11) | Must precede step 8, which references `--batch --apply`. |
| 8 | CHANGE 8 (M-8) | Depends on step 7. |
| 9 | CHANGE 9 (M-9) | Protects the section step 8 writes into. |
| 10–20 | CHANGE 10 – CHANGE 20 | Mutually independent; any order. |
| 21 | CHANGE 21 | Runs last — the new checks assert the state produced by steps 1–20. |

### Two accepted extensions beyond the audit

Both widen the audit's stated B-3 fix and are in scope. They are same-defect-class
completions, not new features:

1. **B-3 is fixed for all four agents, not just Claude Code (CHANGE 1a–1c).** The
   audit's B-3 fix names only Claude Code. Verification showed `~/.codex/skills/` has the
   identical total gap: `sync.sh` steps 4 and 4b deploy workflows and principles, and
   step 4c deploys a global `AGENTS.md` from a template — no rules file reaches Codex
   either. Windsurf and Devin have a narrower version of the same gap (all eight rules
   globally, but only three at project-setup time). The deployment matrix in CHANGE 1
   is the authority on target state, and the acceptance criterion is stated per agent.

   Rationale for treating this as one fix rather than three: `workflow-globals`'s Context
   Bootstrap is declared **mandatory for every phase invocation**, and the loss is not
   only context loading — **Blocker Reconciliation** exists only in
   `rules/phase-atomic-execution.md:44-62` and is cited as authoritative by
   `phase-atomic-execution.md:51` and `pae-implement.md:64`. On any agent missing that
   file, a blocked subtask always falls back to asking the user, defeating the
   auto-reconciliation design. A fix that leaves even one agent uncovered leaves the
   autonomy guarantee false on that agent.

2. **The Context Bootstrap table gains a skill-name column (CHANGE 1d).** Five basenames
   collide between `workflows/` and `rules/` (`phase-discovery.md` and the other four
   phase files). Without the `rule-` prefix, deploying rules as skills would silently
   overwrite the workflow skills; with the prefix, a bare reference to `phase-discovery`
   becomes ambiguous between the rule and the workflow. The extra column resolves the
   ambiguity at the point of reference, and Group 18 of `validate-contracts.sh` guards
   both halves (prefix present, mapping documented).

### Verification after applying

1. `bash validate-contracts.sh` → exit 0 (all groups, including the three new ones).
2. `bash sync.sh`, then walk the CHANGE 1 deployment matrix cell by cell:
   ```bash
   ls ~/.claude/skills/ | grep -c '^rule-'          # expect 8
   ls ~/.codex/skills/  | grep -c '^rule-'          # expect 8
   ls ~/.codeium/windsurf/global_rules/*.md | wc -l # expect 8 rules + principles
   # collision check — these must differ (rule vs workflow, same basename):
   diff ~/.claude/skills/rule-phase-discovery/SKILL.md \
        ~/.claude/skills/phase-discovery/SKILL.md     # expect: files differ
   ```
   Then run `setup-new-project.sh` in a scratch directory and confirm all eight rule
   files land in both `.windsurf/rules/` and `.devin/rules/`.
3. End-to-end smoke on a scratch project: run `/phase-discovery` on a single-phase spec →
   `state-archive.md` present, `## Subtask Progress` populated, `discovery: complete`.
4. End-to-end smoke on a spec that produces a Type 2 composite → `[composite]` block
   present after decomposition; `/phase-execution` reaches `execution: complete` with
   integration validation triggered exactly once.
5. Interrupted-run smoke: mark every subtask `reviewed` with `execution: in-progress`,
   run `/phase-execution` → it calls `/pe-finalize` and reaches `execution: complete`.
6. Multi-phase smoke: run `/phase-pipeline` on a spec with two `## Phase N` headings →
   `task-<basename>-p1/` created with `active_phase: 1` and `spec_phase_count: 2`.
