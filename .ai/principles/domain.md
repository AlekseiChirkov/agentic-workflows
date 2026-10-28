# domain.md — vocabulary and invariants of the pipeline

## Purpose
The precise meaning of every term the workflows use, and the invariants that must hold
across the system. Use these words exactly; a new term needs an entry here before it
appears in a rule.

## Vocabulary

| Term | Meaning |
|---|---|
| **Workflow** | A slash-command definition in `workflows/`; deployed as a Windsurf workflow and a Claude Code / Codex skill. Executable. |
| **Rule** | An always-on contract in `rules/`; deployed as a Windsurf global rule and a `rule-<name>` skill. |
| **Principle** | An engineering standard in `principles/`; deployed as a global rule and a `principle-<name>` skill. |
| **Spec** | The immutable task statement, `.ai/specs/<NN>-<slug>.md`; H1 title required; only `/spec-sync` may edit it after Discovery starts. |
| **Task directory** | `.ai/tasks/todo/task-<NN>-<slug>/` holding `state.md`, `plan.md`, `state-archive.md`, and `T-XX-<slug>/description.md` per subtask. |
| **Phase** | Discovery, Execution, or Validation. Each is a separate command; transitions are human-initiated except under `/phase-pipeline` and `/spec-run`. |
| **Atomic cycle** | The per-subtask sequence: atomic execution (`pae-tests` → `pae-implement` → `pae-finalize`) then atomic validation (`pav-check` → `pav-propose` → `pav-close`). |
| **Leaf** | A subtask with no children; the unit that runs an atomic cycle. |
| **Composite (Type 2)** | A subtask owning leaf children `T-XXa…`; has integration-level Acceptance Criteria checked by `/phase-composite-validation`; never nested (depth-2 cap). |
| **Type 3 re-slice** | A cross-repo producer/consumer pair split by capability into slices; all leaves, grouped by the `Slice` column. |
| **Tripwire** | Runtime detection in `/pae-implement` that a leaf is actually a composite; triggers the Composite Promotion Protocol. |
| **Flow tier** | `full` (default, complete pipeline) or `quick` (four-condition gate, inline contract, inline TDD, no decomposition). |
| **Quick gate** | ≤3 files incl. tests; no new invariant; no behaviour change to a shipped pipeline; no schema change/migration. All four must hold. |
| **RED** | A test that exists, was run, and failed for the expected reason. |
| **GREEN** | Every test from the RED set passes; the set is intact and unweakened. |
| **Pinned** | Characterization tests that pass before a behaviour-preserving change and must keep passing. |
| **`n-a`** | The test-level gate returned `none` with a recorded justification. |
| **Test-level gate** | `unit` → `integration` → `contract` → `smoke` → `none`, first match wins. |
| **Guard** | The first section of a child workflow: checks prerequisites, detects done work, asks before overwriting. |
| **Protected section** | A `state.md` field or section `/compress-state` may never remove or summarize. |
| **Orchestrator** | The `/spec-run` agent: owns sequencing, git, every shared file; never writes code. |
| **Arbiter** | Long-lived context holder; answers class-A questions only, always with a citation. |
| **Implementer** | One sub-agent per subtask running the atomic execution cycle; pauses once at RED. |
| **Validator** | A separate sub-agent per subtask running atomic validation without the Implementer's reasoning. |
| **Class A** | Missing context — the answer exists in project artifacts; the Arbiter resolves it. |
| **Class B** | Missing intent — only the human may decide; harvested into `## Open Questions (batch)` during Discovery. |
| **Batch gate** | The one planned stop of `/spec-run`: all class-B questions presented at once, before the first branch. |
| **Stack** | Subtask branches chained in dependency order; branch N is cut from the tip of N-1 after N-1 is `reviewed`. |
| **`base_commit`** | The sha at branch creation, written once, never recomputed; the only input that makes `/restack` merge-strategy-agnostic. |
| **Fix-task** | A `T-XX-fix-<slug>` subtask created by `/pv-create-fixes` from an approved review issue. |
| **Run log** | The central JSONL store written by `scripts/log-step.sh`; read only by `/retro`. |
| **Retro** | `/retro` — aggregates the run log and recommends edits to this repository; never applies them. |
| **Context Bootstrap** | The ordered `.ai/` load list a phase performs before touching any file; defined per phase in `rules/phase-*.md`. |
| **Context pack** | `.ai/context-pack.md` — a manifest-verified cache of bootstrap sources 1–7. |
| **Umbrella** | The root `.ai/` of a multi-repo project; loaded before the service's own `.ai/`. |
| **Sync** | `scripts/sync.sh` — validate then deploy this repository to all harness locations. |

## Invariants

1. Implementation is never the first step of an atomic cycle (test-first, all modes).
2. A RED set is frozen during GREEN; any amendment carries a `tdd: test amended` note.
3. A phase never auto-advances into the next phase, except inside `/phase-pipeline` and
   `/spec-run`, which declare it.
4. Every workflow reads `state.md` before writing anything, and resumes rather than restarts.
5. Exactly one writer per shared file at any moment; sub-agents return deltas.
6. Proposal `--batch` means record, prompt for nothing, apply nothing. The separate
   `/pae-tests --batch` flag suppresses duplicate digest display only; all evidence gates hold.
7. `notes:` and `target_files:` are always written, even when empty; `atomic-tests:` is
   never removed or downgraded; git fields are touched only by `/spec-run` and `/restack`.
8. No pipeline identifier and no tool attribution ever enters a consumer repository.
9. Repository-owned `.ai/` tracking policy is authoritative. Tracked knowledge and state are accepted; untracked consumer state stays local unless the owner authorizes tracking. This source repository preserves and tracks its complete knowledge base.
10. Logging never blocks a run; durations are never model-written.
11. A rule or vocabulary is defined in exactly one place; every other mention cites it.
12. A `none` test level and a `quick` tier are always justified in writing; an
    unjustified one is a validation finding.
13. `scripts/validate-contracts.sh` must pass before any deploy.
