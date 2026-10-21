# state-archive — task-02-run-log-vocabulary-validation

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis

### Goal
Make run-log writes conform to one exact, documented field contract, add read-only validation for stored records, and make retrospective metrics exclude invalid records without changing historical logs or blocking a workflow.

### Affected Parts
- `scripts/log-step.sh` — validate and normalize producer arguments before state changes; preserve non-blocking writes; add a read-only linter using the same runtime vocabulary.
- `workflows/retro.md` — lint the filtered run corpus, disclose incomplete telemetry, and exclude invalid lines from metric calculations.
- `rules/run-log.md` — document field presence, types, enumerations, normalization, validation behavior, and lint output.
- `scripts/validate-contracts.sh` — compare the helper's effective enumerations and mappings with structured documentation tables and fail on drift.
- `tests/log-step.sh` — add an isolated executable smoke harness for producer, linter, reporting, contract-drift, and historical-file guarantees.

### Codebase Analysis
Files read: 4/12 (4 entry-points, 0 deeper).
- `scripts/log-step.sh` — read as the producer entry point. It currently accepts unknown arguments, does not validate field vocabularies, updates sequence metadata before append, has no step-name check or linter, and removes active metadata after attempting a close append without verifying persistence.
- `workflows/retro.md` — read as the sole consumer entry point. It aggregates the filtered corpus directly and currently has no lint step, invalid-line exclusions, or partial-telemetry reporting.
- `rules/run-log.md` — read as the current contract. It permits arbitrary short gate verdicts and does not specify the required closed enums, count bounds, normalization table, or lint contract.
- `scripts/validate-contracts.sh` — read as the contract-gate entry point. It already uses structured checks and retains nonzero failure status; it has no run-log vocabulary drift check.

The project state records ten existing runs and warns that several contain values outside the current vocabulary. The source contract also requires historical logs to remain unchanged. No `tests/` directory exists, so the acceptance harness will be new. The relevant accepted telemetry decisions align with the spec; the spec supplies the binding field-level details for this task.

### Open Questions
None. The spec defines the vocabulary, validation and write semantics, lint diagnostics, retrospective treatment, documentation checks, and smoke-test coverage.

## Archived Solution Design — Variants

**Variant 1 — Keep the structured runtime contract in the helper.** Define field names, enums, integer fields, bounds, and legacy mappings once in `scripts/log-step.sh`. Producer validation and lint consume those definitions; the contract validator reads the helper's structured contract export and compares it with the documented tables.

Advantages: One effective runtime source for both writes and lint; no new runtime dependency or module; the existing contract gate can compare the definitions it actually uses. Disadvantages: The helper needs a stable structured export for contract checks. Risks: If the export does not represent effective runtime values, contract checks could give false confidence.

**Variant 2 — Add a shared shell contract module.** Move structured definitions into a new shell file sourced by the helper and contract validator, with lint using the same functions.

Advantages: Clear separation between contract data and command behavior; one reusable source. Disadvantages: Adds a runtime file and source-path handling. Risks: A missing or incompatible module could break the helper in otherwise valid installations.

**Variant 3 — Parse the documentation tables at runtime.** Make the tables in the run-log rule the source consumed by writes and lint, then validate the parsed tables.

Advantages: Documentation and runtime behavior share the same textual source. Disadvantages: Couples runtime execution to Markdown parsing and document layout. Risks: A formatting edit could break logging, and the validator would have less independent evidence of agreement.

## Archived Solution Design — Rejected

- Variant 2 was rejected because the task needs no separate runtime module, and introducing one increases file and path coupling.
- Variant 3 was rejected because Markdown parsing would make runtime logging depend on document formatting.
- Event-by-event and document-operation subtasks were rejected because they fragment shared contracts and create extra boundaries around one helper and one canonical table set.

## Integrated validation before input boundary repairs

## Contract Check

Fresh independent verification of `65a6e68c3cdfa775a8ff7685e01203a3d83fe09c..30df897` on `fix/path-argument-progress`. The parent was validation-in-progress. The earlier critical stop is preserved as history by the sole shared-state writer; both original defects are now resolved.

Validation context loaded: project architecture and memory state, architecture/coding/domain principles, ADR index, runbook, task contract and specification, `rules/tdd.md`, and `principles/testing-standards.md`. Required implementation surfaces read: `scripts/log-step.sh`, relevant added gate/producer/lint/retrospective/harness sections of `scripts/validate-contracts.sh`, `tests/log-step.sh`, `rules/run-log.md`, `workflows/retro.md`, and the `docs/USAGE.md` delta.

Fresh evidence:

- `bash tests/log-step.sh`: exit 0, all 23 isolated checks pass; `/tmp/orchestrail-integrated-focused.log`.
- `bash scripts/validate-contracts.sh --run-log-contract-only`: exit 0, `run-log contract: pass`. The focused harness independently executes bidirectional drift mutations, each of which must return nonzero with a field-specific explanation.
- `bash -n scripts/log-step.sh scripts/validate-contracts.sh tests/log-step.sh`: exit 0.
- Full-suite evidence `/tmp/orchestrail-path-full.log`: 574 passed, 0 failed, 2 configured hygiene skips. Inspected; the complete suite was not repeated in this review because the 23 relevant checks and drift gate were independently executed against unchanged source.
- One extra isolated POSIX directory-access probe reproduced the acceptance gap described below.

All executed helper calls use temporary stores. This review neither read the real historical corpus nor changed project source, tests, shared state, git, installed skills, or deployment. Historical preservation is assessed from changed-file boundaries, operation ordering, and isolated checksum assertions, without claiming a real-corpus checksum audit.

### Invariants

| Invariant | Status |
|-----------|--------|
| A rejected event has no event-file or active-metadata side effects | PASS: complete producer argument validation precedes initialization, lookup-dependent writes, sequence increments and persistence. Producer/required-argument/repair tests compare full temporary-store hashes, including existing digests, and verify the next accepted sequence/duration. |
| Logging error paths return zero and emit no success-shaped output | PASS: producer persistence/fallback tests pass, unknown dispatch uses a constant redacted diagnostic, and the bounded path grammar fixes the former loop. The two repair tests exercise absent/populated stores with timeouts, exact safe stderr and empty failure stdout. |
| Runtime writes and lint use one effective vocabulary and mapping source | PASS: `RUN_LOG_CONTRACT` drives producer normalization, event-specific enums, counts and lint; the effective-definition mutation changes an enum and confirms both producer and lint honor it. |
| Lint is read-only, and retrospective metrics include only usable observations | PASS: lint never initializes storage or writes files; each fixture invocation compares checksums. Retrospective intersects diagnostics with exact selected paths and excludes invalid lines; incomplete coverage conservatively admits no records to metrics. Counter/test denominators and physical unusable closes are tested. |
| Existing historical logs remain byte-for-byte unchanged | PASS within the authorized review boundary: no historical-log path is changed in the aggregate diff; tests isolate stores and assert per-operation checksums; acceptance harness overrides inherited stores before helper calls. No historical repair/migration path was introduced. Real historical checksums were not read. |
| The contract validator remains a gate whose drift failures return nonzero | PASS: canonical gate passes independently; mutation tests independently require nonzero for removed, extra, changed and duplicate documentation/runtime values and mappings, including overbroad prefix semantics. |

### Parent Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| 1. Strict producer enums/counts, exact aliases and provenance, rejection before state changes | PASS: producer enum/count/alias/required-argument tests cover canonical values, exact aliases, ordered existing-note provenance, zero/boundary values, malformed counts, duplicate/unknown/missing arguments, and unchanged storage. |
| 2. Flow default, failed-start output and recoverable rejected closes | PASS: flow/persistence checks cover omitted/empty `unknown`, inherited unrestricted multiline flow, metadata text boundaries and legacy compatibility, failed-start empty stdout, rejected close preservation and later accepted close. |
| 3. Dynamic helper workflow membership and advisory behavior | FAIL (important): `check_step_name` tests directory existence and readability but omits search permission. A readable directory without execute permission causes a current known workflow to receive the unknown-name warning instead of the required verification-unavailable warning. The valid event still persists. See reproduction below. |
| 4. Lint selectors, safe ordered JSON diagnostics, exact summary and partial coverage | PASS: all four lint checks cover selectors, active/closed matching files, no-match/empty corpus, strict physical-line JSON, exact bounded integral forms, safe stable diagnostics and distinct invalid-line counts, missing/broken jq, inaccessible files/directories, broken links and mid-file checker failure; hashes remain unchanged. |
| 5. Filtered retrospective diagnostics and honest usable metrics/close classification | PASS: executable loader tests exercise individual and combined filters plus limit, exact file intersection, invalid-line exclusions, optional-counter/test denominators, unavailable/partial/changing stores, lower bounds and invalid physical closes distinct from abandonment. Prose applies eligibility rules to all metric tables and retains recommendation-only behavior. |
| 6. Exact documentation and bidirectional effective drift gate | PASS: canonical JSON tables match the shared export; all removed/extra/changed/duplicate values and mappings are tested on each side; equivalent overbroad prefix mutations still fail the semantic boundary probe. Presence rules, numeric syntax/bounds and lint contract are documented. |
| 7. Executable isolated acceptance harness and historical preservation | PASS: executable runner copies source into a disposable checkout, sets temporary helper/log/workflow roots before invocation, runs each discovered check in a fresh errexit shell and cleans scratch on exit/signals. The focused 23-check run passes; the full-suite meta-test additionally verifies hostile inherited stores, failure propagation and interrupted cleanup. |
| 8. Required acceptance commands and shell syntax pass | PASS: actual isolated harness and changed-script syntax independently pass; inspected fresh full-suite evidence is 574/0/2. No new source changes intervene. |

### Specification Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| 1. Four outcome and three gate legacy cases with deterministic provenance | PASS: exact normalization tests cover every mapping, both aliases in one event, existing notes, unmapped lookalikes, whitespace/punctuation boundary cases and canonical no-provenance behavior. |
| 2. Exact event-specific enums, pinned tests and bounded integer syntax | PASS: complete producer matrix and lint field matrix cover the prescribed values and rejected spellings; malformed arguments write nothing. |
| 3. Missing/empty start flow becomes inherited `unknown` | PASS: flow tests cover omitted and explicit empty start flow across start, step and close, plus unrestricted nonempty flow preservation. |
| 4. Invalid invocation warns once, exits zero, leaves accepted state unchanged | PASS: producer validation, required arguments and both dedicated repair regressions pass exact stderr/stdout/status and checksum assertions. The old unknown-command disclosure and missing-path loop are resolved. |
| 5. Failed starts print no ID; rejected end can close later; errors do not block | PASS: persistence tests cover blocked/unwritable storage, no-jq fallback, missing event files, rejected then valid end and digest failure after a persisted close. |
| 6. Current/synthetic/advisory step membership and unavailable directory warning | FAIL (important): unavailable membership is misclassified when the workflows directory has read permission but lacks search permission. Ordinary current/synthetic/unknown/missing-directory fixtures pass. |
| 7. Read-only lint selectors, stable diagnostics and accurate summary | PASS: all four lint acceptance functions independently pass, including file/line ordering, distinct-invalid-line counts and coverage failures. |
| 8. Filtered retrospective invalid-row reporting and usable denominators | PASS: all four retrospective executable scenarios independently pass; guidance states excluded/missing observation denominators and physical close rules. |
| 9. Exact rule documentation and enum/mapping drift detection both ways | PASS: independent gate and all contract mutation scenarios pass; no separate lint vocabulary exists. |
| 10. Executable isolated harness with specified behavior/checksum fixtures | PASS: actual 23-check runner passes, covers the enumerated scenario categories, never depends on the actual historical corpus and preserves fixture hashes. Add the unsearchable-directory case when repairing criterion 6. |
| 11. Required harness/full-contract/syntax commands succeed without real-log dependence | PASS: harness and syntax independently pass; full command evidence is 574/0/2. The harness and relevant full-suite fixtures redirect helper/store choices into disposable paths. |

### Off-limits

Five parent bullets are represented as six checks by splitting the combined raw-diagnostics/single-source bullet.

| Constraint | Status |
|------------|--------|
| Do not rewrite historical logs or change checksums | PASS: aggregate file scope excludes logs; read-only operations and temporary fixtures preserve checksum snapshots. No actual historical logs were accessed in this review. |
| Do not make writing depend on jq | PASS: shell-only JSON fallback remains; missing-jq writes persist correctly, while lint reports unavailable honestly. |
| Do not let invalid events advance accepted sequence/timestamp/digest/active state | PASS: validation precedes writes and accepted-event progression; comprehensive full-store hashes and deterministic-clock regression pass. |
| Do not echo arbitrary raw values in diagnostics | PASS: producer/parser messages use fixed field/reason tokens; lint serializes paths/coordinates without field values; unknown-command regression verifies raw control-character text never enters stderr. |
| Do not introduce independent runtime vocabulary definitions | PASS: producer and lint consume `RUN_LOG_CONTRACT`; documentation is canonical comparable data and the gate compares its complete key/value set. |
| Do not block callers or make retro automatically edit implementation | PASS: the two former critical failures are repaired; bounded argument parsing, zero-exit error paths and persistence tests pass. Retro still explicitly recommends and stops without applying changes. |

### Original Critical Failures Recheck

- Unknown command redaction: RESOLVED. The current final dispatch emits `log-step: command invalid-command` regardless of input; the 28-case frozen regression passes.
- Missing path operand loop: RESOLVED. The current parser validates complete argument cardinality before lookup and returns safely on missing operands; the 42-case frozen regression passes.

### Remaining Acceptance Failure Reproduction

**important — unavailable workflow membership is reported as an unknown step**, `scripts/log-step.sh:251`.

Reproduce as an ordinary user in isolated storage:

```python
from pathlib import Path
import os, subprocess, tempfile
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    workflows = root / 'home' / 'workflows'
    workflows.mkdir(parents=True)
    (workflows / 'known.md').write_text('Fixture workflow\n')
    env = dict(os.environ, ORCHESTRAIL_HOME=str(workflows.parent),
               ORCHESTRAIL_LOG_ROOT=str(root / 'store'))
    helper = str(Path('scripts/log-step.sh').resolve())
    run = subprocess.run(['bash', helper, 'run-start', '--pipeline', 'fixture'],
                         env=env, capture_output=True, text=True).stdout.strip()
    workflows.chmod(0o400)
    try:
        result = subprocess.run(['bash', helper, 'step', '--run', run,
                                 '--step', 'known', '--outcome', 'ok'],
                                env=env, capture_output=True, text=True)
        print(result.returncode, repr(result.stdout), repr(result.stderr))
    finally:
        workflows.chmod(0o700)
```

Actual: exit 0, empty stdout, `log-step: step name is not in the current workflow list\n`; event persisted.
Expected: exit 0, event persisted unchanged, exactly one `log-step: step-name verification unavailable\n` advisory because directory entries cannot be searched. Add `-x` to the directory availability condition and a regression fixture for readable-but-unsearchable workflow directories. The existing missing-directory test does not cover this permission combination.

Step 1 (Contract Verification) complete: **29 PASS, 2 FAIL, 0 critical failures**, across 6 invariants, 8 parent criteria, 11 specification criteria and 6 off-limits checks. Both failed entries describe the same important defect. No critical stop is needed. Root must apply this delta and reconcile the historical `pause` field before code review begins.

## Code Review

Independent whole-change review of `65a6e68c3cdfa775a8ff7685e01203a3d83fe09c..30df897` on `fix/path-argument-progress`.

Guard satisfied: the sole shared-state writer applied the fresh Contract Check, moved the original critical pause into Validation History, and left active invariants/off-limits passing before authorizing this step. Validation remains in progress. The decision remains the helper-owned structured contract, shared by writes and lint and compared with canonical documentation.

Validation context loaded: architecture, memory state, architecture/coding/domain principles, ADR index, runbook, task/spec contracts, `rules/tdd.md` and `principles/testing-standards.md`. Reused the completed bootstrap without redundant rereads, then inspected the current active guard and source. No project writes, git changes, deployment, installed-skill changes or real-log access occurred.

### Findings

1. **important — documented flag telemetry prevents starting a run**, `scripts/log-step.sh:126`; affected documented callers include `rules/run-log.md:81` and `workflows/spec-run.md:41`.

   `parse_arguments` treats every operand beginning with `--` as a missing operand, regardless of which option receives it. The documented `--flags "--step-by-step"` and actual spec-run flag text therefore cause the entire otherwise valid run-start to be rejected. The same check rejects unrestricted nonempty flow labels such as `--custom-flow`, and similarly restricts other free text. This is a regression from the existing free-text interface; it can silently remove complete runs from telemetry for workflows that have flags in force.

   Reproduce with an absent temporary log root:

   ```bash
   scratch=$(mktemp -d)
   ORCHESTRAIL_LOG_ROOT="$scratch/store" bash scripts/log-step.sh run-start \
     --pipeline phase-discovery --flags '--step-by-step'
   rm -rf "$scratch"
   ```

   Actual: exit 0, empty stdout, one `log-step: run-start flags missing-operand` warning and no store/run. Repeated independently with `--flags '--allow-pr --dry-run'` gives the same result. `--flow '--custom-flow'` similarly produces `log-step: run-start flow missing-operand` and no run.

   Expected: documented flag text is retained as supplied and the start persists, with a usable ID; nonempty unrestricted flow labels are preserved through start/step/end. Missing operands must still be rejected without consuming the next helper option. Repair the argument grammar and its documented caller syntax together as needed, preserving supported callers and the rejection safety boundary. Add behavior tests for the exact documented flag examples and dash-leading free text; the existing missing-operand, unknown-argument and no-side-effect assertions must remain intact.

2. **important — inaccessible workflow verification is misreported as unknown membership**, `scripts/log-step.sh:251`; missing regression in `scripts/validate-contracts.sh:2335`.

   The directory check tests existence/read permission without testing search permission. With a readable but unsearchable workflows directory, Bash can list names but `-f` cannot inspect their entries. A current known workflow is then reported as an unknown step. The event is correctly persisted and the message remains safe, but the specified unavailable-verification behavior is violated. This is the same issue already recorded in parent acceptance criterion 3 and specification criterion 6, not an additional distinct contract defect.

   Exact isolated reproduction as an ordinary user:

   ```python
   from pathlib import Path
   import os, subprocess, tempfile
   with tempfile.TemporaryDirectory() as temporary:
       root = Path(temporary)
       workflows = root / 'home' / 'workflows'
       workflows.mkdir(parents=True)
       (workflows / 'known.md').write_text('Fixture workflow\n')
       env = dict(os.environ, ORCHESTRAIL_HOME=str(workflows.parent),
                  ORCHESTRAIL_LOG_ROOT=str(root / 'store'))
       helper = str(Path('scripts/log-step.sh').resolve())
       run = subprocess.run(['bash', helper, 'run-start', '--pipeline', 'fixture'],
                            env=env, capture_output=True, text=True).stdout.strip()
       workflows.chmod(0o400)  # readable directory, no execute/search permission
       try:
           result = subprocess.run(['bash', helper, 'step', '--run', run,
                                    '--step', 'known', '--outcome', 'ok'],
                                   env=env, capture_output=True, text=True)
           print(result.returncode, repr(result.stdout), repr(result.stderr))
       finally:
           workflows.chmod(0o700)
   ```

   Actual: exit 0, empty stdout, `log-step: step name is not in the current workflow list\n`; the step persists. Expected: one `log-step: step-name verification unavailable\n` warning and the same persisted step. Require directory search permission alongside readability and add a mode-0400 fixture; preserve known/synthetic/unknown/missing-directory cases.

### Review Coverage

- **Architecture and clarity:** one readonly `RUN_LOG_CONTRACT` drives normalization, enums and numeric bounds; lint receives those definitions rather than maintaining another vocabulary. Canonical table comparison is field-specific and bidirectional, with explicit prefix-boundary probes. Metadata escaping preserves text boundaries without evaluating caller values. No new runtime module/dependency was added to the producer.
- **Security and errors:** safe eight-hex IDs precede metadata lookup; caller values are not sourced/evaluated; JSON strings escape controls; rejected complete producer arguments precede mutations. New dispatch redaction and bounded path parsing resolve the original critical defects. Lint reports paths through JSON and excludes raw field values. Read/write failures remain nonblocking, and partial OS writes/locking remain outside the requested redesign.
- **Lint edge cases:** reviewed raw-physical-line handling, literal NUL detection, malformed JSON numeric extensions, exact numeric lexeme validation above jq precision, huge exponents, negative zero, final missing newline, empty/no-match corpora, inaccessible/broken selected paths, initial and mid-file tool failures, and distinct line/violation counts. The four executable lint scenarios pass independently with checksum assertions.
- **Retrospective honesty:** reviewed exact selected-path intersection, all filters before filename limit, invalid-row exclusion, conservative exclusion of all unverified observations, known lower bounds, affected-run labels, usable counter/test/duration denominators, physical invalid close versus abandonment, unreadable close status and selection limitations. Guidance retains small-corpus warnings, raw-context restrictions, missing measurements and recommendation-only operation. The four executable scenarios pass independently.
- **Test integrity:** all seven leaves have actual smoke tests; no unjustified `n-a` exemption exists. Independent frozen comparisons retain all original lines of the five producer functions from `6b7b548`, four lint functions from `93c985c`, three contract functions from `75703d6`, and the acceptance meta-test from `8d8cf60`. The retrospective frozen block from `f096c89` removes only `def load(**filters):`, replacing it with `def load(expect_mutation=False, **filters):` to add explicit intentional-mutation verification; no original assertion/case is removed. The current complete validator is byte-identical to the final repair RED commit `9af9998`; the preceding unknown-command regression remains present and unchanged alongside the additive path regression. Recorded unrelated fixture amendments explain actual fixture defects, and transient added numeric expectations were reconciled with mathematical JSON integrality without weakening frozen tests. No vacuous sole assertions, skip/xfail weakening, or repository mocks were found.
- **Acceptance harness integrity:** dynamic test discovery includes the two repairs; fresh Bash processes keep assertion failure meaningful despite callers using conditionals; temporary checkout/store/workflows override inherited roots; cleanup covers success/failure/signals. The full-suite meta-test checks hostile inherited stores and intentionally masked failures. New findings expose missing behavior cases rather than removed tests.

### Verification

- Independently ran the real `bash tests/log-step.sh`: **23 passed, exit 0**, evidence `/tmp/orchestrail-integrated-focused.log`.
- Independently ran the canonical contract gate and changed-script syntax checks: passed.
- Inspected unchanged-source full-suite evidence `/tmp/orchestrail-path-full.log`: **574 passed, 0 failed, 2 configured hygiene skips**. Full repeat was unnecessary after the focused rerun and no source edits.
- Independently reproduced both remaining findings in temporary stores. Original disclosure/hang regressions pass within the actual isolated harness.
- No real historical corpus was read. Preservation conclusions use changed-file scope, isolated full-store checksums and source ordering rather than claiming an actual historical checksum audit.

### Summary

Step 2 (Code Review) complete: **2 findings — 0 critical, 2 important, 0 optional**. Both require repair before review readiness. The fresh Contract Check has one existing acceptance defect represented by two failed rows; finding 1 adds a separate producer compatibility/flow-contract failure discovered during code review. Neither introduces a critical invariant/off-limits failure, so the completed review can proceed to issue consolidation and approved repairs.
