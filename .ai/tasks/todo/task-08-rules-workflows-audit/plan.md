## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status | Model (Claude) | Model (Codex) |
|----|------|---------------------|------------|--------| --- | --- |
| T-01 | Inventory extractor | suite helpers → guard and CLI → audited set and readers → text model → git reads → atomic inventory write | — | reviewed | claude-opus-5-5 |  |
| T-02 | Reference edges | spans → span grammar → heading resolution → token grammar → status and flags → contexts → load flag | T-01 | reviewed | claude-opus-5-5 |  |
| T-03 | Candidates, legacy mentions and duplicate clusters | call clauses → repeated loads → full-output and harness lines → legacy mentions → text units → clusters | T-02 | reviewed | claude-opus-5-5 |  |
| T-04 | Verifier: assessment consistency | valid fixture → verify frame → schema and staleness → rows and sections → loads, candidates, repetition, legacy → groups → findings → coverage, installed, economics | T-03 | reviewed | claude-opus-5-5 |  |
| T-05 | Verifier: map, amendments and statement coverage | fixture specification → map shapes → split cover → collisions and prefixes → deviation → amendments → statement coverage | T-04 | reviewed | claude-opus-5-5 |  |
| T-06 | Renderer and report checks | render helpers → eighteen subsections → render CLI → layout parsing → review, blockers, region checks → per-code completeness | T-05 | reviewed | claude-opus-5-5 |  |
| T-07 | Extraction and assessment of rules and adapters | clean extraction → assessment skeleton → read 14 rules → read adapters → loads → candidates and legacy → findings → verify | T-06 | reviewed | claude-opus-5-5 |  |
| T-08 | Assessment of workflows | read orchestrators → read phase children → read utilities → loads → candidates → repetition review → findings → verify | T-07 | reviewed | claude-opus-5-5 |  |
| T-09 | Map, findings, amendments and report | duplicate groups → defaults → map decisions → statement coverage → amendments → blocking flags → report and render → verify exits 0 | T-08 | reviewed | claude-opus-5-5 |  |
| T-10 | Index, knowledge and review line | index line → script rows → runbook note → inventory sentence → memory entries → review line → verify, suite, validator → permitted-paths check | T-09 | reviewed | claude-opus-5-5 |  |
| T-11 | Fix: git read isolation | lazy-fetch and rename guard → filter guard or narrowed claim → tests first | T-10 | reviewed | claude-opus-5-5 |  |
| T-12 | Fix: review follow-ups (blockers, evidence, runbook) | tests first → two-way blockers check → evidence resolution → constants and runbook note | T-11 | reviewed | claude-opus-5-5 |  |
| T-13 | Fix: extraction edge cases (proposals) | tests first → adapter lstat → pruned explicit-stack reader walk → token boundary, bare home, separator rows, stop marker | T-12 | reviewed | claude-opus-5-5 |  |
| T-14 | Fix: git isolation follow-ups and version matrix (proposals) | tests first → NUL cut, stat before open, CR/LF strip → below-top-level unknown → docstring boundary → runbook bullet → container matrix | T-13 | reviewed | claude-opus-5-5 |  |
| T-15 | Fix: verify input and form rules (proposals) | tests first → kind change, no-follow inputs → amendment rules → ASCII digits, line bound → recorded amendments | T-14 | reviewed | claude-opus-5-5 |  |
| T-16 | Fix: output boundary and render (proposals) | characterization and red tests → Zs/Cf escapes, quoted values, output-unwritable → cell backslashes, sorting, write-protected report, economics region → suite cache | T-15 | reviewed | claude-opus-5-5 |  |
| T-17 | Fix: audit output corrections and fresh review (proposals) | scripted assertion red → assessment edits → render → gate → independent review → review line | T-16 | reviewed | claude-opus-5-5 |  |
| T-18 | Feat: state tool memory consistency warning (proposals) | tests first → read-only memory parse → leaf comparison → warning code | — | reviewed | claude-opus-5-5 |  |
| T-19 | Fix: separator pattern shadowing (reconciliation finding) | tests first → own name for the terminology pattern → re-point duplicate and statement units | T-17 | reviewed | claude-opus-5-5 |  |

## Execution Strategy

Strictly sequential in listed order; every subtask depends on the one before it. T-01–T-06 build the tool and its suite test-first and share two files, so they never run concurrently. The tool and suite are committed before T-07 extracts, because the extraction must run on a clean tree and every later artefact is pinned to that revision. T-07–T-09 share the single assessment file and have one writer at a time. T-10 runs after the independent validation of T-09, because it records that verdict and commit in the report, and it makes the index and knowledge edits last, because those files are readers of the extraction. No parallel execution is claimed.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-01 | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | core inventory with one byte-stable output |
| T-02 | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | one grammar, one `edges` list |
| T-03 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | one heuristic layer producing the candidate lists |
| T-04 | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | per-item assessment rules share one valid fixture and one done-state |
| T-05 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | rules that read the migration specification file; own fixtures |
| T-06 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | report file round trip and its checks |
| T-07 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | pinned snapshot plus the 19 rule and adapter files |
| T-08 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | the 42 workflow files and the repetition review |
| T-09 | leaf | S1=9, S2=1, S3=1, S4=false, S5=1 | cross-file synthesis ending in a silent `verify` |
| T-10 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | closure edits gated by the review verdict |

Ten leaves instead of the target of eight, resolved by the Autonomous Decision Protocol:

- **Chosen — ten leaves.** Each has one testable component and one criteria cluster. The verifier alone carries about forty diagnostic codes; one leaf for it would exceed fifteen steps and hold three criteria clusters (per-item rules, map and amendment rules, report rules).
- **Rejected — merge the extractor's three parts into one leaf.** Inventory, reference grammar and candidate detection each have their own fixtures and done-state; merged, the leaf would have three components and about thirty steps.
- **Rejected — merge the two reading groups.** Reading 61 files with every load edge and candidate in one leaf leaves no intermediate verified state; the split follows the file groups the specification names and keeps one writer.
- **Rejected — fold the closure into the report leaf.** The review line needs the verdict and commit of an independent validation that happens only after the report leaf is complete.
- **Rejected — composites.** No candidate has two independently testable components after the split above, so no parent with integration criteria is needed; the integration check of the whole is the silent `verify` of T-09 and the final gates of T-10.
- **Rejected — splitting the task in two (tool, then audit run).** The specification is one delivery whose acceptance needs both; the tool has no consumer other than this audit.

Sources: `workflow-reference → ## Decomposition Rules`, `workflow-reference → ## Autonomous Subtask Classifier`, the specification's implementation-order hint, P4 and P7.
