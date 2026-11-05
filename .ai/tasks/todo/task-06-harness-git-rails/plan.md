## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status |
|----|------|---------------------|------------|--------|
| T-01 | Git-rails harness capability record | confirm docs facts → failing contract checks → Claude section + Codex line | — | reviewed |
| T-02 | Command parser and invocation resolver | suite + validator mode → grammar/registry RED → tokenizer, parser, resolver, git-read layer, R31, I3 | — | reviewed |
| T-03 | Staging and commit rules | AC-04/AC-05 RED → operand checks R01–R07 → message sources, P1–P3, R08–R10 | T-02 | reviewed |
| T-04 | Push target resolution and protected refs | AC-06 RED → remote/refspec/push.default resolution → protected set → R11–R19, lease interface | T-02 | reviewed |
| T-05 | Destructive, ref-rewrite and merge operations | AC-08 RED → R20–R25, R27–R30 → exception-verifier and replay-verifier interfaces | T-02, T-04 | reviewed |
| T-06 | Restack journal verification | AC-07 RED → journal discovery/schema → replay and lease verifiers | T-04, T-05 | reviewed |
| T-07 | Hook entrypoint, adapter and diagnostics | AC-01/02/09–12 RED → entrypoint fast paths → adapter + allowlist → diagnostics, limits, failure modes | T-01, T-02, T-03, T-04, T-05, T-06 | reviewed |
| T-08 | PreToolUse registration and per-event installer validation | installer RED → manifest entry → per-event validation → source check | T-01, T-07 | reviewed |
| T-09 | Owned permission deny fragment | AC-13/14 RED → fragment → deny merge, receipt v2, v1 migration, removal | T-01, T-08 | reviewed |
| T-10 | Safety-rails contract and restack journal documentation | contract checks RED → git-flow Enforcement + owner protocol → restack schema → readers → full suite | T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09 | reviewed |
| T-11-fix-push-and-pull-resolution-gaps | Push and pull resolution gaps | failing rows → last-colon refspec split, merge qualification, pull program and updateRefs checks, config push programs, relative redirects, pipefail pin, lease failure on R17 | T-10 | reviewed |
| T-12-fix-installer-and-contract-hardening | Installer and contract hardening | failing cases → readable physical entrypoint, logging pinned to continue, wildcard deny rules rejected, dry-run note | T-11-fix-push-and-pull-resolution-gaps | reviewed |

## Execution Strategy

Strictly sequential in table order (T-01 → T-10) as one stack: each leaf branches from the
preceding reviewed tip; T-01 branches from `main`. Order follows spec §14: harness facts
first (its stop condition must be cleared before adapter code), core rules next, the process
boundary after every reason code exists, installation after the entrypoint exists, and the
textual contract last so it describes shipped behaviour.

Shared-file constraints: `hooks/git_rails.py` and `tests/git-rails.sh` are extended by
T-02–T-07; each later leaf adds rules or cases and never weakens an earlier leaf's frozen
cases. `scripts/validate-contracts.sh` is touched by T-01, T-02, T-07 and T-10;
`scripts/install-hooks.py` and `tests/hook-install.sh` by T-08 and T-09. Only the
orchestrator writes `state.md`, `plan.md`, `.ai/memory/*`, `.ai/adr/*` and `.ai/specs/README.md`;
workers return deltas. No parallel execution.

Model selection: `scripts/model-catalog.py` reported `selection_available: false` (no local catalog at `~/.config/orchestrail/model-catalog.md`, 2026-11-03), so no model column is written and every Implementer is an ordinary session-default worker without a model override; no requested or actual model identity is claimed. Arbiter and Validators are session-default role workers.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-01 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One capability record verified by one contract-check cluster; prerequisite fact gate of spec §14 step 2 |
| T-02 | leaf | S1=10, S2=1, S3=1, S4=false, S5=1 | One substrate component (event → resolved invocation records / parser-level decisions); registry gate, grammar and suite wiring all assert that component's output |
| T-03 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | Staging and commit rules share operand classification (R07 reuses R01–R02); one rule family |
| T-04 | leaf | S1=7, S2=1, S3=1, S4=false, S5=1 | Push resolution and protected refs form one decision path; AC-06 is one cluster |
| T-05 | leaf | S1=8, S2=1, S3=1, S4=false, S5=1 | Owner-authorizable non-push operations share the protected-ref function and one AC cluster (AC-08) |
| T-06 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | One journal record verified by two checks over the same schema; AC-07 is one cluster |
| T-07 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | The hook process boundary (stdin → exit/stdout/stderr) is one component; fast path, protocol, diagnostics and failure modes are all observable only at that boundary |
| T-08 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | Hook-manifest ownership; independent of permission ownership |
| T-09 | leaf | S1=6, S2=1, S3=1, S4=false, S5=1 | Permission-deny ownership and receipt v2; independently testable from T-08 |
| T-10 | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | One textual contract update pinned by one check cluster |
| (count) | 10 leaves, no merge to 8 | — | Autonomous Decision Protocol: V1 ten leaves (Simplicity 4, Reversibility 4, Fit 5, Testability 5, Blast 4 = 22) vs V2 eight leaves merging T-05+T-06 and T-08+T-09 (3, 3, 3, 3, 4 = 16). V2 merges independently testable components (S2=2, S5=2), which the classifier would turn into composites; V1 keeps healthy leaves and matches the spec's suggested (a)–(h) split plus the two installer/rule-family splits. Winner V1. |
| (spec suggestion) | adopted with two splits | — | Suggested (c) kept; (d) split into push (T-04) and other operations (T-05) because R20–R30 are a separate AC cluster (AC-08); (g) split into hook registration (T-08) and deny fragment (T-09) because AC-13 hook part and AC-14 are independent; (e) restack documentation moved to T-10 so T-06 stays code-only |
