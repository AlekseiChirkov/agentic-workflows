# Telemetry implementation plan

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Type | Status |
|---|---|---|---|---|---|
| T-01 | Usage contract | (children: T-01a, T-01b, T-01e, T-01f, T-01h, T-01i, T-01j, T-01k, T-01l, T-01m, T-01n, T-01o, T-01p, T-01q, T-01r, T-01s, T-01g, T-01c, T-01d) | — | composite | reviewed |
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
| T-02 | Bounded source adapters | (children: T-02a, T-02b, T-02c) | T-01d | composite | reviewed |
| T-02a | bounded explicit source selection | validate inputs → compute → integrate | T-01d | leaf | reviewed |
| T-02b | profile-driven source normalization and quarantine | validate inputs → compute → integrate | T-02a | leaf | reviewed |
| T-02c | normalization destination safety | reproduce race → protect destination → validate | T-02b | leaf | reviewed |
| T-03 | Immutable publication and lifecycle projection | integrate → verify → review | T-02 | leaf | reviewed |
| T-04 | Usage resolution, ownership and exact pricing | integrate → verify → review | T-03 | leaf | reviewed |
| T-06 | Retrospective reports and duration analysis | integrate → verify → review | T-04 | leaf | reviewed |
| T-07 | Current status and warning delivery | integrate → verify → review | T-04, T-06 | leaf | reviewed |
| T-08 | Compatibility, recovery and operating guidance | integrate → verify → review | T-03, T-04, T-06, T-07 | leaf | reviewed |

## Execution Strategy

The contract composite passed independent integration validation. Execute the approved source-adapter destination-safety fix, then rerun its composite integration validation before the publication work item. The existing publication branch predates this newly discovered fix; reconcile the stacked branch with the reviewed fix before resuming it without changing its recorded original base_commit. The five remaining work items group the original acceptance clusters by capability. Independent work may proceed in parallel in isolated worktrees; integration and review follow dependency order. The user explicitly requested this consolidation despite the normal leaf-health classifier: each grouped work item retains multiple independently testable clusters and must be independently reviewed in full. No previous progress or branch history is discarded.

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
| T-02c | fix sibling | one independently reproduced integration defect | Automatically approved important source-adapter integration fix; the parent remains open until revalidated. |
| T-03 | consolidated leaf | multiple components and acceptance clusters | User-requested grouping; retain all original criteria and tests in the description and archived records. |
| T-04 | consolidated leaf | multiple components and acceptance clusters | User-requested grouping; retain all original criteria and tests in the description and archived records. |
| T-06 | consolidated leaf | multiple components and acceptance clusters | User-requested grouping; retain all original criteria and tests in the description and archived records. |
| T-07 | consolidated leaf | multiple components and acceptance clusters | User-requested grouping; retain all original criteria and tests in the description and archived records. |
| T-08 | consolidated leaf | multiple components and acceptance clusters | User-requested grouping; retain all original criteria and tests in the description and archived records. |
