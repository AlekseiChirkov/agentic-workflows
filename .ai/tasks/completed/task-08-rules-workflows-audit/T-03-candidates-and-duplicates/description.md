## Goal
`extract` lists repeated-load, full-output and harness-name candidates, legacy mentions and verbatim duplicate clusters.

## Context
- Dependencies: T-02 (resolved command edges, load edges and span positions).
- Constraints: Python 3.11+ standard library only; type annotations on every function; functions small and single-purpose; `python3 -I` invocation; data-contract names fixed by the specification (JSON keys, diagnostic codes, id prefixes) are used verbatim, while comments, docstrings and test names state rules in words without requirement, criterion or specification labels. Source contract: spec DM-6 with its call-clause, negation and stop-marker rules and its unit-splitting rules.
- Reason: Candidate and cluster detection is one heuristic layer over the edges with one done-state: the five candidate lists for a fixture tree equal the expected lists.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** call detection and `RL-NNN` pairs; `FO-NNN` and `HN-NNN` lines; legacy mentions for the three terms; text units and `DUP-NNN` clusters; ordering and id assignment; completion of the DM-1 object.
- **Out of scope:** dispositions, roles and groups, which are the auditor's; transitive or deeper-than-one-step repeats, which are found by reading.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write failing cases for the call fixture, the candidate lines, the legacy terms and the shared sentence.
2. Compute each command edge's clause with spans replaced by spaces, and decide a call by call verb, absence of a negation before the verb in the clause and absence of an earlier `**stop**` marker on the line.
3. Restrict callers to workflows with at least one `Invocation:` line and callees to other workflows.
4. For each distinct caller-callee pair and each target both load through single-target load edges, emit an `RL` entry ordered by caller, callee, target.
5. Emit `FO` and `HN` entries for matching lines outside fences and front matter, with whitespace collapsed and text cut to 160 code points.
6. Emit legacy mentions with source, line, column, lowercased term and text for audited Markdown and JSON files.
7. Build text units: table rows, and paragraphs stripped of quote markers, indentation and list markers, joined, collapsed and split after sentence punctuation; drop units under eight words.
8. Group equal units into clusters with members in path then line order, order clusters by first member and number them from `DUP-001`.
9. Write the five lists into the inventory in DM-1 key order and re-check byte-identical repeat runs.

## Acceptance Criteria
- Given workflows `w-root` ("Run `/w-child`."), `w-child`, `w-a` and `w-b` that run each other, all loading `` the `r-one` rule ``, and `workflows/HUB.md` without an `Invocation:` line that runs both commands, the candidates are exactly `RL-001` (`w-a` → `w-b`), `RL-002` (`w-b` → `w-a`) and `RL-003` (`w-root` → `w-child`), each with target `rules/r-one.md`.
- In `w-root`, the lines "see `/w-child`", "Do not run `/w-child`" and "**stop**: run `/w-child` first" add no call, while "If no file remains, run `/w-child`." and "Run `/w-child`. It does not ask." are calls.
- A line "paste the full test output" yields `FO-001`, and a line naming "Codex" yields `HN-001`.
- A fixture rule containing `Windsurf`, `.devin/` and `devinly` yields exactly two legacy mentions.
- Two fixture rules sharing a sentence of eight or more words yield one `DUP-001` cluster listing both; a shared sentence of seven words yields none.
- Two `extract` runs on the candidate fixture are byte-identical.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - call fixture → exactly three `RL` ids with the stated pairs
  - negation, stop marker and verb-less mention → no call; negation outside the verb clause → call
  - candidate lines → `FO-001`, `HN-001`
  - legacy fixture → two mentions
  - shared sentence at and below the threshold → one cluster, none
  - repeat run → identical bytes
- **Edge cases:** call cycle; graph without calls; load edge with two targets; candidate text inside a fence or front matter; table separator rows; heading lines; list-marker and quote stripping; sentence split on `.`, `!`, `?`; unit repeated twice in one file.
