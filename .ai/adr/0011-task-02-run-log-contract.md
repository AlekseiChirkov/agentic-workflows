# ADR-0011: Decisions for Task 02 — Run-log contract validation

## Status

Accepted

## Date

2026-10-21

## Related Task

- Task: [Run-log vocabulary validation](../tasks/todo/task-02-run-log-vocabulary-validation/state.md)
- Related pull requests: #13, #14, #15, #16, #17, #18, #19, #20.
- Related files: `scripts/log-step.sh`, `scripts/validate-contracts.sh`, `rules/run-log.md`, `workflows/retro.md`, `tests/log-step.sh`, `docs/USAGE.md`.

## Summary

Validate telemetry before writing, report historical violations without changing them, and calculate retrospective metrics only from usable observations. One runtime contract defines the producer and linter vocabulary; a structured documentation gate and isolated executable acceptance checks detect drift.

## Context

Historical telemetry contains noncanonical values, while logging must remain optional and nonblocking. Strict event vocabularies, exact legacy normalization, safe diagnostics, unchanged historical files and honest retrospective denominators are binding requirements. Writing must continue without jq; lint may require jq and must disclose unavailable checks.

## Decisions

### Decision 1: Keep effective vocabulary in the helper

**What was decided:**
Use the helper's readonly associative contract for producer validation, exact aliases, lint and the sorted `contract` export (`scripts/log-step.sh:43`, `scripts/log-step.sh:761`).

**Why:**
The comparison gate must inspect the definitions actually used by both consumers. Keeping them in the existing helper adds no runtime module or dependency.

**Alternatives:**
A separate shell module adds another deployment unit. Parsing documentation at runtime couples logging to Markdown. Independent validator or lint enums can drift silently.

**Consequences:**
Future vocabulary changes must update the shared definitions and canonical documentation tables together. The export is a read-only verification interface.

**Related files:**
- `scripts/log-step.sh:43`
- `rules/run-log.md:116`
- `scripts/validate-contracts.sh:121`

### Decision 2: Reject complete invalid invocations before state changes

**What was decided:**
Validate complete producer arguments before metadata lookup or writes, normalize only exact aliases with ordered provenance, and preserve arbitrary nonempty flow text. Fixed-header escaped active metadata preserves record boundaries. Failures return zero with safe diagnostics; start IDs require persisted events and usable metadata. Known helper options remain reserved while ordinary dash-leading operand text is preserved. Workflow membership requires directory read and search access. Auxiliary path parsing uses a bounded grammar (`scripts/log-step.sh:156`, `scripts/log-step.sh:364`, `scripts/log-step.sh:430`, `scripts/log-step.sh:744`).

**Why:**
Invalid observations must not advance timing or sequence state. Caller text must not become metadata records or diagnostics. Logging must not block callers, including malformed auxiliary invocations.

**Alternatives:**
Dropping individual invalid fields would accept a partially invalid event. Raw multiline metadata permits record collisions. Echoing unknown arguments discloses caller text. An open-ended shifting parser can hang on missing operands.

**Consequences:**
Callers must use canonical values and put contextual verdict text in notes. Rejected closes remain retryable. Ordinary legacy metadata remains readable; event JSONL retains its schema. General locking and rollback after partial operating-system writes remain outside scope.

**Related files:**
- `scripts/log-step.sh:156`
- `scripts/log-step.sh:364`
- `scripts/log-step.sh:744`

### Decision 3: Treat historical validation as read-only evidence

**What was decided:**
Lint checks physical JSONL records without normalization or mutation, including strict JSON syntax and exact bounded integer values. It reports examined counts and partial or unavailable coverage. Retrospective loading intersects diagnostics with the selected corpus and excludes invalid or unverified observations from metrics (`scripts/log-step.sh:785`, `workflows/retro.md:54`, `workflows/retro.md:194`).

**Why:**
Invented canonical values, guessed coverage and invalid denominators produce misleading recommendations. A physically present unusable close must remain distinct from a missing close.

**Alternatives:**
Migrating old logs violates immutability. Treating unchecked records as clean hides tooling failures. Treating invalid closes as abandonment changes the meaning of the metric.

**Consequences:**
Incomplete lint or a changing corpus may leave metrics unmeasurable. Reports disclose exclusions and usable denominators. Historical logs are never repaired automatically; retrospective output remains recommendations only.

**Related files:**
- `scripts/log-step.sh:785`
- `workflows/retro.md:54`
- `workflows/retro.md:194`

### Decision 4: Verify drift and behavior through isolated executable checks

**What was decided:**
Compare canonical JSON Markdown tables bidirectionally with the runtime export, including alias-prefix boundary probes. Run focused behavioral checks through a disposable checkout and temporary source/log roots, with separate Bash processes, checksum guards and signal cleanup (`scripts/validate-contracts.sh:121`, `tests/log-step.sh:1`).

**Why:**
Mention checks cannot prove effective vocabulary agreement. Independent shell processes ensure assertion failures propagate even when the runner is called from a conditional. Temporary fixtures protect real telemetry.

**Alternatives:**
Scattered greps miss missing or extra values. Copying test implementations into a second runner invites divergence. Running against real historical logs creates privacy and mutation risks.

**Consequences:**
New focused checks are discovered by the runner. Runtime and documentation mutations must fail the gate. Tests require Bash, Python and jq in the validation environment; the producer retains its optional-jq fallback.

**Related files:**
- `rules/run-log.md:116`
- `scripts/validate-contracts.sh:121`
- `tests/log-step.sh:1`

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| May existing tracked changes be adopted into the run? | The owner approved continuing with them. | Preserve and review the changes on the feature stack. |
| Should validation findings require another permission stop? | The owner requested fixing everything and finishing the task. | Repair reproducible defects with frozen regressions and independent review; retain the no-merge boundary. |

## Rejected Options

Duplicate runtime vocabularies, documentation parsing during writes, historical-log migration, guessed metrics, raw caller diagnostics and real-log test fixtures were rejected for the reasons above.

## Implications for Future Work

Keep event vocabularies and canonical tables synchronized. Preserve nonblocking diagnostics, legacy metadata compatibility and read-only lint behavior. Future telemetry fields must define eligibility and denominators explicitly. Hook-based recording and cost accounting remain separate work.

## Verification

The executable acceptance harness passes 25 focused checks. The complete contract suite passes 576 checks with zero failures and two configured hygiene skips. All shell scripts pass syntax checks; whitespace and task artifact checks pass. Independent reviews cover all original leaves and both critical auxiliary-command repairs. Historical data was not accessed by fixtures.

## References

- Task: run-log vocabulary validation.
- Pull requests: #13 through #20, in dependency order.
- Related documents: run-log rule, retrospective workflow, architecture principles on nonblocking logging and executable enforcement.
