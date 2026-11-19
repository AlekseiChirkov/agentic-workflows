## Goal
`extract` records every reference to an audited file as an edge with its form, context, status, flags and targets.

## Context
- Dependencies: T-01 (text model, node names and inventory writer).
- Constraints: Python 3.11+ standard library only; type annotations on every function; functions small and single-purpose; `python3 -I` invocation; data-contract names fixed by the specification (JSON keys, diagnostic codes, id prefixes) are used verbatim, while comments, docstrings and test names state rules in words without requirement, criterion or specification labels. Source contract: spec DM-4 (span grammar, token grammar, edge status, defect predicate, grammar flag) and DM-5 (spans, extents, load lines).
- Reason: The reference grammar is one component with one done-state: the `edges` list for a fixture tree equals the expected list.

Off-limits: no change to `rules/`, `workflows/`, `harness/`, `templates/`, `principles/`, `hooks/`, `tests/`, `scripts/validate-contracts.sh`, `scripts/sync.sh`, any other existing script or any specification; no registration of a check in the validator or in sync; never run `scripts/sync.sh`, an installer, a workflow or a model for the inventory; never read or change installed copies; no absolute path and no former repository name in any output; fixtures use synthetic stems, never this repository's names.

## Scope
- **In scope:** node names; single-backtick spans; span grammar forms `command`, `section-ref`, `rule-name`, `path`/`glob`, `bare-name`; token grammar forms with masking; heading resolution through extents with `resolved`, `resolved-prefix`, `heading-unmarked`, `missing-heading`; edge status for shared stems; `md_suffix`; `in_spec09_grammar`; contexts including `check-description` and `comment` for a validator-named reader; the `load` flag from load lines; a defect-predicate helper used by later subtasks.
- **Out of scope:** candidates, legacy mentions, duplicate clusters; any judgment about whether a defect edge is a real defect.
- **Target files:** `scripts/audit-instructions.py`, `scripts/check-audit-instructions.py`

## Steps
1. Write failing cases: one fixture span or token per form and status, the control example, and the context cases.
2. Derive rule stems, workflow stems and audited paths from the inventory entries.
3. Extract spans per line outside fences and front matter, treating double-backtick spans as two empty spans, and record `column` as the code-point offset of `raw`.
4. Implement span forms 1–5 in order, first match wins, with the slash-prefixed section reference going to `section-ref`.
5. Resolve section-reference components per candidate through heading extents and compute each candidate's worst `heading_status`.
6. Implement the token grammar over all remaining text, form by form with masking and whole-token boundaries; use it alone for non-Markdown sources.
7. Compute `status` (including `ambiguous-stem` for two candidates), `md_suffix`, `in_spec09_grammar` and `targets` in path order.
8. Assign contexts `front-matter`, `fence`, `span`, `text`, and the two validator contexts for `scripts/validate-contracts.sh`.
9. Mark `load: true` on span edges of load lines in audited Markdown files.
10. Emit `edges` ordered by source path, line and column, and expose the defect predicate as one function.

## Acceptance Criteria
- Given `` `alpha-flow → ## Missing` `` in a fixture workflow where `rules/alpha-flow.md` lacks that heading, the edge has status `missing-heading` and the defect predicate holds.
- Fixture spans and tokens for every form yield the form, context, status, `md_suffix` and targets the grammar defines: `ambiguous-stem` for a shared stem, `resolved` for the same stem followed by ` rule`, `resolved-prefix` (not a defect), `heading-unmarked` (a defect), `unknown-command`, `missing-target`, `missing-path`, `glob-empty`.
- `` `/w-one → ## Step 1` `` is a `section-ref`, never a `command`; `` `rules/r-one.md` `` has `md_suffix: false` and `` `w-one.md → ## Step 1` `` has `true`.
- The same span has `in_spec09_grammar: true` in `rules/r-one.md` and `false` in `docs/G.md`; `` `state.md → ## X` `` yields no edge.
- In a fixture `scripts/validate-contracts.sh`, a name inside the first quoted string after `check ` has context `check-description` and a name on a `#` line has context `comment`.
- References inside a fenced block have context `fence`; references from planning and history readers are recorded and the defect predicate is false for them.
- A span edge on a line containing the word `load` or `read` outside spans has `load: true`; the same span on another line has `false`.

## Test Plan
- **Level:** unit, integration
- **Scenarios:**
  - control example → `missing-heading` and defect
  - one case per form and status → expected edge fields
  - slash-prefixed section reference and suffix flags → as stated
  - grammar flag by source location; document reference → no edge
  - validator contexts → as stated
  - fence, planning and history → never defects
  - load line → `load: true`
- **Edge cases:** stem without a hyphen; stem shared by a rule and a workflow; head with `rule-` prefix or directory path; glob with `*` not crossing `/`; path containing `<`; existing directory path; unmarked component after a resolved heading; token adjacent to `_` or `-`; unclosed fence; CRLF line; undecodable reader.
