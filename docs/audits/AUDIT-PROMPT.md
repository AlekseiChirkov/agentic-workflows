# Audit prompt — `/spec-run`

Paste everything below the line into a fresh agent session opened in the repository root.

---

# Independent audit — the `/spec-run` orchestrated workflow

You are an independent auditor. You did not design this workflow and you owe its author
nothing. Your job is to find where `/spec-run` is **wrong, internally inconsistent, or
impossible to execute as written**, and to write what you find into a report file.

**You are auditing, not repairing.** Do not edit any workflow, rule, template, or script. The
only file you create is the report. If a fix is obvious, describe it in the report and move on.

Work only inside the repository root. Do not run `scripts/sync.sh`. Do not touch `~/.claude/`,
`~/.codex/`, `~/.codeium/`, or anything outside this directory. You may copy the repository to
a scratch directory and experiment there.

---

## 1. What `/spec-run` is

`/spec-run` carries one spec from Discovery to review-ready pull requests using
context-bounded sub-agents, creating one stacked git branch per subtask. It is the only
orchestrator that performs git writes (with `/restack`, which repairs the stack afterwards).

Four roles, each a context boundary rather than a personality: the **Orchestrator** owns
sequencing, git, and every shared file; the **Arbiter** holds full project context for the
whole run and may answer only with a cited source; the **Implementer** runs one subtask's
`pae-tests` → `pae-implement` → `pae-finalize`; a **separate Validator** runs `pav-check` →
`pav-propose` → `pav-close` without having seen how the code was written.

Sub-agents exist to bound context, **not** to parallelise — execution is strictly sequential
because `## Subtask Progress` has no locking.

The system is entirely markdown instructions. There is no runtime, so every defect is a defect
of *specification*: a step that cannot be performed, an order that contradicts itself, a value
read that nothing writes, a stop that no one declared.

## 2. The surface you must read

Read all of it before judging any part. Most defects here are **relational** — a sequence
defined in one file and consumed differently in another — and are invisible when a file is
read alone.

**Primary:**
- `workflows/spec-run.md` — the workflow itself
- `workflows/restack.md` — its repair counterpart
- `rules/orchestration.md` — roles, shared-file discipline, class A/B escalation
- `rules/git-flow.md` — preflight, branch model, commits, PRs, safety rails

**Everything `/spec-run` invokes or depends on:**
- Discovery: `pd-analyze`, `pd-decompose`, `pd-design`, `pd-finalize`, `pd-archive`
- Model selection: `pd-select-model`
- Per subtask: `pae-tests`, `pae-implement`, `pae-finalize`, `pav-check`, `pav-propose`,
  `pav-close`, `phase-composite-validation`
- Task level: `phase-validation`, `pv-contract`, `pv-review`, `pv-issues`,
  `pv-classify-fixes`, `pv-create-fixes`, `pv-execute-fixes`, `pv-finalize`
- PR text: `suggest-pr-description`
- State hygiene: `compress-state`

**Contracts the above are written against:**
- `rules/workflow-globals.md` (canonical status formats, mode-override registry, `--batch`)
- `rules/workflow-reference.md` (protected sections, status translation, marker list)
- `rules/tdd.md`, `rules/quick-flow.md`
- `workflows/PIPELINE.md`, `docs/USAGE.md`, `docs/SPEC-RUN-QUICKSTART.md` — documentation that must
  agree with the workflow

`scripts/validate-contracts.sh` holds the executable checks. Run it (`bash scripts/validate-contracts.sh`) to
see the current baseline; it should report zero failures. A passing suite is not evidence of
correctness — several checks have been found to pass against an inverted contract.

## 3. Method

### 3.1 Trace one run end to end

Before looking for defects, write out — for yourself — exactly what happens on a run of a
three-subtask spec with `--allow-pr`: every file read, every file written, every agent spawned,
every commit, in order. Most contradictions surface while doing this, because you are forced to
name the state each step depends on and to check that an earlier step produced it.

Then do the same for a run where subtask 2 contains a composite with two children.

### 3.2 Map writers to readers

For every value `/spec-run` reads, name the workflow that writes it and confirm the format
matches: `plan.md → Model`, `## Open Questions (batch)`, `branch:`, `base_branch:`,
`base_commit:`, `commits:`, `pr:`, `target_files:`, `atomic-tests:`, `## Subtask Progress`
statuses, `## Issue List → ### Approved`, `## Fix-Tasks`. A value read but never written, or
written in one shape and parsed in another, is a defect.

### 3.3 Run the scenario bank

For each scenario below, answer in one line: **does the workflow say what happens, and is it
executable?** A scenario the workflow does not cover is a finding; so is one where two files
give different answers.

1. The test-level gate returns `none` for a subtask — what commits exist, and what does the
   PR's test-evidence section say?
2. The Validator returns NEEDS WORK on subtask 2 of 5 — what state are branches, PRs, and
   `plan.md` left in, and what does re-running do?
3. Subtask 3 is the last child of a composite — who runs the integration validation, on which
   branch, and who writes its results?
4. Two subtasks derive the same branch slug from their Goals.
5. `--dry-run` is passed before Discovery has ever run.
6. `--dry-run` is passed *after* a complete run.
7. The run is interrupted between the RED commit and the GREEN commit — where does Step 0
   resume, and is that derivable from recorded state?
8. The run is interrupted after `/pav-close` but before the draft PR is opened.
9. The human squash-merges PR #1 while the run is still building subtask 4.
10. A class-B ambiguity surfaces during Execution.
11. `/pv-issues` produces only `optional` findings.
12. `/pv-classify-fixes` groups four fixes into one shared branch — where does that branch
    attach, in what order, and who validates it?
13. A subtask ends `blocked`.
14. The spec is multi-phase (two or more `## Phase N` markers).
15. `--allow-pr` is passed but `gh auth status` fails at Step 7 rather than at preflight.
16. A repository tracks `.ai/` knowledge and state, while a consumer keeps its state
    untracked. Verify preflight accepts both and sync preserves each tracking policy.
17. A subtask's `target_files:` is empty when the orchestrator goes to stage the commit.
18. The Arbiter cannot answer a class-A question with a citation.

### 3.4 Attack the check suite

Pick the checks in `scripts/validate-contracts.sh` that claim to guard `/spec-run` behaviour. For each:
copy the repo to a scratch directory, **delete or invert the contract the check names**, and
re-run the suite. If it still passes, the check is vacuous — record it as a finding with the
regression it failed to catch. Delete the scratch copy afterwards. Do not modify the suite.

## 4. What to look for

Work through these deliberately. For each, state what you checked, not only what you found.

1. **Sequence integrity.** Do Steps 0–8 depend only on state produced by earlier steps? Does
   any step reference an artifact a *later* step creates?
2. **The RED checkpoint.** The Implementer pauses at RED so the orchestrator can build a
   test-only commit. Verify this is achievable as written: who holds the test file list, what
   guarantees no implementation file exists yet, and what happens when the same agent is
   resumed.
3. **Role boundaries.** Does any sub-agent get instructed — directly or through a workflow it
   invokes — to write a shared file, run git, or read context its role denies it?
4. **Resume and reconciliation.** Is every resume point derivable from recorded state? Does
   Step 0's git-vs-state reconciliation cover partial writes, and what does it do about a
   subtask whose `commits:` is recorded but whose branch is gone?
5. **Git safety.** No merge, no push to base, no force-push outside `/restack`, no branch
   deletion, no `git add -A`, no `git reset --hard`, no `git clean`. Verify nothing in the
   invocation chain contradicts the rails, including workflows `/spec-run` calls indirectly.
6. **The stop model.** `/spec-run` claims the batch gate is its only planned stop. Enumerate
   every place a child workflow waits for a human, and check each is either overridden by a
   declared rule or listed as a deliberate stop. An undeclared wait makes the autonomy claim
   false.
7. **`--batch` semantics.** One meaning everywhere: record everything, prompt for nothing,
   apply nothing. Check no caller reinterprets it, and that anything recorded is eventually
   surfaced or deliberately abandoned.
8. **Identifier leaks.** No subtask id, spec name, task directory, ADR number, or `.ai/` path
   may reach a branch name, commit message, or PR body — in instructions or in examples.
9. **Unenforceable instructions.** A step no agent can perform deterministically, or a gate
   whose criteria cannot be evaluated from available inputs. Where the system replaces judgement
   with a checkable gate elsewhere, an un-gated judgement call here is a defect.
10. **Documentation agreement.** `PIPELINE.md`, `docs/USAGE.md`, and `docs/SPEC-RUN-QUICKSTART.md` must
    describe the workflow that exists. A doc promising behaviour the workflow does not implement
    is a finding against the doc.

## 5. Write the report

Create **`SPEC-RUN-AUDIT.md`** in the repository root, in English, with this structure:

```
# /spec-run — audit, <YYYY-MM-DD>

## Verdict
<3–5 sentences: is the workflow executable as written, and what is the worst thing wrong>

## Findings
Ranked worst first.

### F<N> — <one-line title>  [critical | important | minor]
**Where:** <file:line, every file involved>
**What the files say:** <quote the conflicting statements>
**Why it is a defect:** <the concrete run that breaks, or the value that cannot be produced>
**Suggested direction:** <one or two sentences — not a patch>

## Scenario results
| # | Scenario | Covered? | Finding |

## Check-suite quality
Vacuous checks found, with the regression each failed to catch.

## Coverage
Which of the ten dimensions you completed, and anything you could not assess — with the reason.

## Not defects
Things that look wrong but are deliberate, with the file that justifies them. This section
keeps the next reader from re-reporting them.
```

**Severity:** *critical* — the workflow produces a wrong result, corrupts state, or cannot
complete; *important* — a contract is unenforceable or two files disagree in a way that will
diverge; *minor* — documentation drift with no behavioural effect.

## 6. Rules for the report

- **Quote before you conclude.** Every finding names files and lines and quotes the text it is
  about. A finding without a citation is an opinion.
- **Do not invent findings to fill the table.** If a dimension is clean, say so in one line.
- **Do not report style preferences.** Wording you would have chosen differently is not a
  defect.
- **State your gaps.** If you could not assess something, say what and why — do not quietly
  omit it. A short honest report beats a padded one.
- **Distinguish "the workflow is wrong" from "I would have designed it differently."** Only the
  first belongs in Findings; the second belongs in `## Not defects` or nowhere.
- Report in English. Put no pipeline identifier into any example commit message, branch name, or
  PR text you write.
