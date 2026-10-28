## Goal
The deterministic selector excludes unsuitable models before comparing qualified economics and retains conservative quality floors under every worsening task signal.

## Context
- Dependencies: T-01 catalog schema and helper contract.
- Constraints: source REQ-03 through REQ-05; retain corrected seven-factor rubric and exhaustive mapping; exact candidate IDs and explicitly supplied actual harness capability snapshot; no model-name inference.
- Reason: selection policy is one pure independently testable component.

Off-limits: shared files, git, real models/providers, learned probabilities, price ledger, automatic switching, weakening security/financial/architecture/core-invariant floors.

## Scope
- **In scope:** seven factors C/A/V/R/Ver/Crit/RW on 1–5; Ver=1 difficult/late and 5 cheap/immediate; total bounded mapping to quality requirements; independent capability evidence; actual availability/context/tools/owner filters; creative/heavy-reasoning/mechanical traits and legacy migration; qualified cost comparison with uncertainty and stronger/default retention.
- **Out of scope:** plan parsing, provider execution, production default changes, measured success probabilities or savings.
- **Target files:** scripts/model_selection.py, scripts/model-catalog.py, tests/model-selection.py, scripts/validate-contracts.sh.

## Steps
1. Freeze exhaustive boundary/monotonicity and eligibility fixtures before implementation, including hard-floor and trait conflict cases.
2. Implement one validated signal definition and total explicit floor mapping, retaining conservative frontier floors for architectural, security, financial and core-invariant tasks.
3. Filter catalog candidates against explicit current request support, context/tools, owner constraints, independent evidenced capability and mandatory floors; unknown availability is ineligible.
4. Compare only qualified cost evidence, treat missing prices as unknown, retain suitable stronger/default choice when economics or quality are uncertain, expose decision reasons and add offline CLI coverage.

## Acceptance Criteria
- Every valid score tuple maps to a defined bounded floor; raising complexity/ambiguity/risk/criticality/rework/context or lowering Ver never lowers the floor; 0/6/nonintegers/booleans are rejected.
- An unavailable cheap model, context/tool-incompatible model, owner-excluded model, and model below a security/financial/architecture/core-invariant floor are excluded before economics; traits cannot bypass these exclusions.
- Equal cost bands/prices never imply equal capability; missing prices are not zero; uncalibrated cost/error judgments cannot replace a suitable stronger/session default; qualified stronger-first remains selectable and decisions state their evidence/uncertainty.
- creative/heavy-reasoning/mechanical overrides and documented legacy trait mapping are validated, including conflicting/unknown traits and empty eligible sets.

## Test Plan
- **Level:** unit, contract.
- **Scenarios:** exhaustive score tuples plus neighboring monotonicity → defined nondecreasing floors; explicit capability snapshots → candidate exclusion reasons; same-price different-evidence and missing-price fixtures → conservative behavior; trait overrides → floor preservation; stronger-first fixture → eligible stronger model.
- **Edge cases:** all boundaries, unknown/default unavailable, no eligible model, empty constraints, context overflow, missing evidence, arbitrary IDs, malformed numeric input, equal economics and conflicting traits.
