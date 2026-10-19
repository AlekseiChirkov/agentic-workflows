# Split rules into always-on contracts and on-demand reference

## Goal

An atomic step can begin with 40–60k tokens of instructions before reading any code.
Much of that is rationale, worked examples, and incident history a step does not need.
Split each rule into a short contract that stays always-on and a reference part loaded
only when cited, declare each workflow's rule dependencies, and measure the result
(ADR-0009, Decision 6).

## Acceptance Criteria

- [ ] Each `rules/*.md` is ≤ 700 words; the always-on set (every rule with
      `load: always`) totals ≤ 6 000 words; everything moved goes to
      `rules/reference/<name>.md`, linked with one line "Rationale and examples:
      `ref-<name> → ## <Section>`"
- [ ] `sync.sh` deploys `rules/reference/*.md` as `ref-<name>` skills (`load: on-demand`)
- [ ] Every workflow's front matter gains `loads:` listing the rules it needs; the
      Context Bootstrap in each `bootstrap-*` rule cites that list instead of restating it
- [ ] `measure-context.sh <workflow>` prints the word count of the workflow plus every
      rule and reference it would load; the totals are recorded in `docs/reference/`
- [ ] For `atomic-execution-implement` and `atomic-execution-tests` the measured total is
      ≤ 50 % of the pre-change value
- [ ] `validate-contracts.sh` enforces the word limits and that every moved section is
      still reachable by its citations
- [ ] Golden-run `flat` (spec 09) shows no behavioural change

## Out of Scope

- Rewriting any contract's meaning
- The `.ai/` bootstrap of consumer projects (`/context-pack`)

## Notes

- Decisions: ADR-0009 Decision 6 (700 / 6 000 words, `rules/reference/` as `ref-*`
  skills, `loads:` key, after spec 13).
- Runs after spec 13 (renames) and needs spec 09 to prove no behavioural change.
- First candidates to move: quick-flow worked examples, the 2026-07-22 incident
  narrative, the TDD "why the order matters" section.
