## Subtasks

| ID | Name | Model | Key Steps (summary) | Depends On | Status |
|---|---|---|---|---|---|
| T-01 | Local catalog storage | | validate schema → inspect freshness → atomic explicit refresh | — | reviewed |
| T-05 | Required archive preservation | | restore English records → translate historical comparisons → verify unchanged identity gate | T-01 | reviewed |
| T-02 | Conservative model selection | | total score mapping → eligibility floors → qualified economic choice | T-01, T-05 | reviewed |
| T-03 | Compatible plan model resolution | | legacy/dual columns → preserve table → visible resolution | T-01, T-02 | reviewed |
| T-04 | Cached selector workflow integration | | compact selector → update readers → offline gates and guide | T-01, T-02, T-03 | reviewed |
| T-06 | Compatible independent-validator wording | | restore existing wording contract → verify unchanged guard → independently review | T-04 | reviewed |


## Execution Strategy
Execute strictly sequentially in table order: T-01, prerequisite T-05, T-02, T-03, T-04. Each leaf branches from the preceding reviewed tip. Only the orchestrator modifies shared state, Git and PRs. Implementers own one component and its tests; validators are independent. All blank Model cells deliberately retain the session default: no usable current local catalog is available and this invocation has no --refresh. Do not claim a different requested or actual execution model.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---|---|---|---|
| T-01 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One catalog persistence/freshness contract |
| T-02 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One deterministic candidate-selection policy |
| T-03 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One compatible plan/request-resolution interface |
| T-04 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One executable caller contract integrating the helpers; documentation and gates verify that same interface |

| T-05 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | Documentation-only prerequisite preserves existing archive/identity consistency; recorded after root-cause analysis and owner autonomous repair authorization |
