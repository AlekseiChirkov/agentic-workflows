# Telemetry implementation plan

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Type | Status |
|---|---|---|---|---|---|
| T-01 | Usage contract | (children: T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d) | — | composite | not-started |
| T-01a | canonical encoding and content identities | validate inputs → compute → integrate | — | leaf | reviewed |
| T-01b | typed usage measurements | define states → validate evidence → test bounds | T-01a | leaf | reviewed |
| T-01e | observation and bundle schema | define envelopes → validate → reject unsafe inputs | T-01b | leaf | reviewed |
| T-01f | source profile schema | define profile → validate evidence → verify fixtures | T-01e | leaf | reviewed |
| T-01h | source selection schema | define fields → validate → verify fixtures | T-01f | leaf | reviewed |
| T-01i | inventory schema | define fields → validate → verify fixtures | T-01h | leaf | reviewed |
| T-01j | attribution schema | define fields → validate → verify fixtures | T-01i | leaf | reviewed |
| T-01k | collection segment schema | define fields → validate → verify fixtures | T-01j | leaf | reviewed |
| T-01l | diagnostic measurement schema | define fields → validate → verify fixtures | T-01k | leaf | reviewed |
| T-01m | price snapshot schema | define fields → validate → verify fixtures | T-01l | leaf | reviewed |
| T-01n | pricing scenario schema | define fields → validate → verify fixtures | T-01m | leaf | reviewed |
| T-01o | warning policy schema | define fields → validate → verify fixtures | T-01n | leaf | reviewed |
| T-01p | analysis corpus schema | define fields → validate → verify fixtures | T-01o | leaf | reviewed |
| T-01q | usage receipt schema | define fields → validate → verify fixtures | T-01p | leaf | reviewed |
| T-01r | lifecycle projection schema | define fields → validate → verify fixtures | T-01q | leaf | reviewed |
| T-01s | current-run snapshot schema | define fields → validate → verify fixtures | T-01r | leaf | reviewed |
| T-01g | producer schema export | expose registry → preserve compatibility → verify parity | T-01s | leaf | reviewed |
| T-01c | versioned source profiles and counter normalization | validate inputs → compute → integrate | T-01g | leaf | reviewed |
| T-01d | typed diagnostic metrics | validate inputs → compute → integrate | T-01c | leaf | reviewed |
| T-02 | Bounded source adapters | (children: T-02a, T-02b) | T-01d | composite | not-started |
| T-02a | bounded explicit source selection | validate inputs → compute → integrate | T-01d | leaf | reviewed |
| T-02b | profile-driven source normalization and quarantine | validate inputs → compute → integrate | T-02a | leaf | reviewed |
| T-03 | Immutable publication | (children: T-03a, T-03b) | T-02b | composite | not-started |
| T-03a | immutable usage bundle publication | validate inputs → compute → integrate | T-02b | leaf | not-started |
| T-03b | validated lifecycle usage projection | validate inputs → compute → integrate | T-03a | leaf | not-started |
| T-04 | Resolution and completeness | (children: T-04a, T-04b, T-04c, T-04d, T-04e) | T-03b | composite | not-started |
| T-04a | response identity and deduplication | validate inputs → compute → integrate | T-03b | leaf | not-started |
| T-04b | stream finality and revisions | validate inputs → compute → integrate | T-04a | leaf | not-started |
| T-04c | cumulative epochs and aggregate coverage | validate inputs → compute → integrate | T-04b | leaf | not-started |
| T-04d | inventory and measurement completeness | validate inputs → compute → integrate | T-04c | leaf | not-started |
| T-04e | causal ownership and late evidence | validate inputs → compute → integrate | T-04d | leaf | not-started |
| T-05 | Pricing and arithmetic | (children: T-05a, T-05b) | T-04e | composite | not-started |
| T-05a | price snapshot and scenario applicability | validate inputs → compute → integrate | T-04e | leaf | not-started |
| T-05b | exact cost computation and completeness | validate inputs → compute → integrate | T-05a | leaf | not-started |
| T-06 | Retrospective analysis | (children: T-06a, T-06b, T-06e, T-06c, T-06d) | T-05b | composite | not-started |
| T-06a | fixed explicit retrospective corpus | validate inputs → compute → integrate | T-05b | leaf | not-started |
| T-06b | versioned retrospective exports | validate inputs → compute → integrate | T-06a | leaf | not-started |
| T-06e | comparable group statistics | select groups → calculate statistics → report coverage | T-06b | leaf | not-started |
| T-06c | independent acceptance and comparison | validate inputs → compute → integrate | T-06e | leaf | not-started |
| T-06d | measured duration and interval coverage | validate inputs → compute → integrate | T-06c | leaf | not-started |
| T-07 | Status and alerts | (children: T-07a, T-07b, T-07c, T-07d) | T-06d | composite | not-started |
| T-07a | collection mode and evidence segments | validate inputs → compute → integrate | T-06d | leaf | not-started |
| T-07b | pure status and threshold episodes | validate inputs → compute → integrate | T-07a | leaf | not-started |
| T-07c | duration warning eligibility | validate inputs → compute → integrate | T-07b | leaf | not-started |
| T-07d | owner-controlled warning delivery | validate inputs → compute → integrate | T-07c | leaf | not-started |
| T-08 | Compatibility and guidance | (children: T-08a, T-08b) | T-07d | composite | not-started |
| T-08a | legacy compatibility and recovery | validate inputs → compute → integrate | T-07d | leaf | not-started |
| T-08b | offline telemetry operating guidance | validate inputs → compute → integrate | T-08a | leaf | not-started |

## Execution Strategy

Independent components may be implemented concurrently in isolated worktrees when their dependencies permit it. Integrate reviewed changes into the sequential branch stack and validate compatibility before completing each parent. The orchestrator is the sole writer of shared state and Git operations. Each leaf follows test-first execution and independent validation. User authorization explicitly permits parallel subagents and final integration to main.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---|---|---|---|
| T-01 | composite (Type 2) | S1=0, S2=19, S3=19, S4=false, S5=19 | Owner-approved redistribution separates independently testable measurements, envelopes, entity schemas and export. |
| T-01a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One canonical encoding and content identities component and one coherent acceptance cluster. |
| T-01b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | Typed measurements form one component after redistribution. |
| T-01e | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | Observation and bundle interchange is one component. |
| T-01f | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One source-profile schema. |
| T-01h | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable source selection schema. |
| T-01i | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable inventory schema. |
| T-01j | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable attribution schema. |
| T-01k | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable collection segment schema. |
| T-01l | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable diagnostic measurement schema. |
| T-01m | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable price snapshot schema. |
| T-01n | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable pricing scenario schema. |
| T-01o | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable warning policy schema. |
| T-01p | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable analysis corpus schema. |
| T-01q | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable usage receipt schema. |
| T-01r | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable lifecycle projection schema. |
| T-01s | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independently verifiable current-run snapshot schema. |
| T-01g | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | Producer contract export is one integration component. |
| T-01c | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One versioned source profiles and counter normalization component and one coherent acceptance cluster. |
| T-01d | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One typed diagnostic metrics component and one coherent acceptance cluster. |
| T-02 | composite (Type 2) | S1=0, S2=2, S3=2, S4=false, S5=2 | Independent components and acceptance clusters require integration. |
| T-02a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One bounded explicit source selection component and one coherent acceptance cluster. |
| T-02b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One profile-driven source normalization and quarantine component and one coherent acceptance cluster. |
| T-03 | composite (Type 2) | S1=0, S2=2, S3=2, S4=false, S5=2 | Independent components and acceptance clusters require integration. |
| T-03a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One immutable usage bundle publication component and one coherent acceptance cluster. |
| T-03b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One validated lifecycle usage projection component and one coherent acceptance cluster. |
| T-04 | composite (Type 2) | S1=0, S2=5, S3=5, S4=false, S5=5 | Independent components and acceptance clusters require integration. |
| T-04a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One response identity and deduplication component and one coherent acceptance cluster. |
| T-04b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One stream finality and revisions component and one coherent acceptance cluster. |
| T-04c | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One cumulative epochs and aggregate coverage component and one coherent acceptance cluster. |
| T-04d | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One inventory and measurement completeness component and one coherent acceptance cluster. |
| T-04e | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One causal ownership and late evidence component and one coherent acceptance cluster. |
| T-05 | composite (Type 2) | S1=0, S2=2, S3=2, S4=false, S5=2 | Independent components and acceptance clusters require integration. |
| T-05a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One price snapshot and scenario applicability component and one coherent acceptance cluster. |
| T-05b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One exact cost computation and completeness component and one coherent acceptance cluster. |
| T-06 | composite (Type 2) | S1=0, S2=5, S3=5, S4=false, S5=5 | Independent components and acceptance clusters require integration. |
| T-06a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One fixed explicit retrospective corpus component and one coherent acceptance cluster. |
| T-06b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One versioned retrospective exports component and one coherent acceptance cluster. |
| T-06e | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One group-statistics component and coherent acceptance cluster. |
| T-06c | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One independent acceptance and comparison component and one coherent acceptance cluster. |
| T-06d | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One measured duration and interval coverage component and one coherent acceptance cluster. |
| T-07 | composite (Type 2) | S1=0, S2=4, S3=4, S4=false, S5=4 | Independent components and acceptance clusters require integration. |
| T-07a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One collection mode and evidence segments component and one coherent acceptance cluster. |
| T-07b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | The pure status result includes policy evaluation and episode transition in one deterministic component; delivery remains separate. |
| T-07c | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One duration warning eligibility component and one coherent acceptance cluster. |
| T-07d | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One owner-controlled warning delivery component and one coherent acceptance cluster. |
| T-08 | composite (Type 2) | S1=0, S2=2, S3=2, S4=false, S5=2 | Independent components and acceptance clusters require integration. |
| T-08a | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One legacy compatibility and recovery component and one coherent acceptance cluster. |
| T-08b | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One offline telemetry operating guidance component and one coherent acceptance cluster. |
