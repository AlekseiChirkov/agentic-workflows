## Goal
The delivered assessment and report carry the content corrections the reviews proposed — exact citations, consequences that match their observations, cross-references between related findings, and amendments to spec 09 whose size-exception condition measures the minimal rule — and the report's review line names a fresh independent review of the corrected outputs.

## Context
- Dependencies: T-16 (the render tool used to refresh the report).
- Source: improvement proposals of T-07 (Optional 1, 2), T-08 (Optional 1, 2) and T-09 (Do Now, Optional 1–4), ordered applied by the owner on 2026-11-18; the owner accepts the report after these corrections. Verified by a read-only planning pass (T-07 Do Later 1 and 2 are already in the outputs; T-08 O1's observation is already corrected):
  - T-07 O1: in AUD-08-017's observation, name the third protocol section (model resolution in `## Parent plan.md Table Format`, mapped to `rules/contract-state-files.md`) and cite AUD-08-028 in the text — not in `evidence` (a finding id in finding evidence is `evidence-unresolved`).
  - T-07 O2: AUD-08-004's closure already cites AUD-08-026; add AUD-08-004 (and AUD-08-036) to AUD-08-026's observation or closure text.
  - T-08 O1: AUD-08-045's `consequence` still says "the other two each follow only the few lines one step wrote"; restate it: the /pav-close pass follows the writes of /pav-check, /pav-propose and /pav-close, and the /pae-finalize pass those of the execution cycle; only the /pe-execute pass follows no write.
  - T-08 O2 (confirmed at 8d7e484: the standalone sentence is `rules/workflow-globals.md:36`, the reuse sentence runs into :37; :35 is "Rules define…"): AUD-08-052 evidence `:35`/`:36` → `:36`/`:37` and its observation `:35-36` → `:36-37`; AUD-08-053 evidence `:35` → `:36` and its consequence `:35-36` → `:36-37`.
  - T-09 Do Now: in AMD-08-03 (third clause), AMD-08-06 and AMD-08-07 the size-exception condition becomes "the front matter, the moved `## Context Bootstrap` section, the `## Phase Behaviors` heading and the citing line alone exceed 300 words".
  - T-09 O1: AMD-08-03 places the exception directly after the limit: "…exactly the two `## ` sections … and, unless DM-20 → Bootstrap size exceptions lists it, at most 300 words (DM-19); …".
  - T-09 O2: AMD-08-01's reason names AMD-08-02 and AMD-08-05 as its set.
  - T-09 O3: AMD-08-05's proposed text adds "in scan set E or R".
  - T-09 O4: remove AC-39 from `affected` of AMD-08-05 and AMD-08-06.
- Inventory re-extraction (orchestrator decision 2026-11-18, carried from T-13): the corrected adapter token boundary removes one false adapter edge that the delivered inventory holds (a reader line at 8d7e484 cites `templates/codex-global-AGENTS.md.bak`), so `verify --strict` at 8d7e484 reports `inventory-stale …inventory.json:82043 a fresh extraction differs from the inventory`. Re-extract the inventory at 8d7e484 with the current tool on a clean checkout (the `extract` output must differ from the delivered inventory by exactly that edge and nothing else; prove it with a JSON diff), replace the delivered inventory with it, re-render the report, and confirm no assessment item refers to the removed edge. After this the gate's allowed strict line (`scratchpad/orch/strict-allowed.txt`) is deleted by the orchestrator and `verify --strict` at 8d7e484 must be silent again.
- Steps for the outputs: edit the assessment JSON (the inventory changes only by the re-extraction above); run `render --write` with the current tool; update the Summary's paraphrase of AMD-08-03 if it quotes the changed condition; add one Method note listing these post-review corrections. New text holds no `$`+digit, no `<n> tokens`, no USD or EUR; no finding id goes into finding `evidence`.
- Review line: the current `Reviewed: Validator 2026-11-18 pass 0add2fa…` attests outputs that these edits change. This subtask's independent Validator reviews the corrected outputs; after a pass the orchestrator moves the review line to the reviewed commit (`Reviewed: Validator <date> pass <sha>`) in a separate commit and re-runs the gate (the review commit must exist on both trees). `Accepted:` stays `pending` here; the owner's acceptance is recorded afterwards.
- Constraints: the inventory changes only by the re-extraction above; `verify` stays silent at 8d7e484 with the outputs overlaid, including `--strict`; the current tree prints only the recorded 14 `inventory-stale` lines.
- Off-limits: every file except the inventory (re-extraction only), the assessment JSON and the report; no specification is edited here.

## Scope
- **In scope:** the content items above and the re-render.
- **Out of scope:** applying amendments to spec 09 (done at acceptance), tool code.
- **Target files:** `docs/audits/2026-11-17-rules-workflows-audit.inventory.json`, `docs/audits/2026-11-17-rules-workflows-audit.assessment.json`, `docs/audits/2026-11-17-rules-workflows-audit.md`

## Steps
1. Test level `none` is not assumed: the delivery gate is the executable check for these outputs; record it as the test with its before/after result (before: gate passes on the uncorrected outputs; the check that the corrections are present is a scripted assertion over the JSON listing each corrected field, run before (fails) and after (passes)).
2. Edit the JSON; render; Summary and Method notes.
3. Gate; scripted assertion; `git diff --stat` shows only the two files.

## Acceptance Criteria
- Every item above is present in the assessment and, where rendered, in the report.
- The delivery gate prints `GATE PASS`.
- No other file changes.

## Test Plan
- **Level:** smoke (scripted assertion over the corrected fields) plus the delivery gate.
- **Scenarios:** each corrected field; render idempotence (a second `render --write` changes nothing).
- **Edge cases:** evidence lines stay within the inventory line counts; no economics pattern in new text.
