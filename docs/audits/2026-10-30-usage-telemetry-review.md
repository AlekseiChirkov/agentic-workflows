# Usage telemetry review

Date: 2026-10-30

## Scope and method

Pull requests #37–#63 introduce optional offline usage normalization, immutable
publication, exact pricing, retrospective reports, duration analysis and warning
delivery. Each pull request received a separate review with an isolated context.
Dependency order was preserved. Each affected pull request then received a
separate repair and an independent recheck before the next repair began.

Reviews compared the proposed changes, their integrated behavior, acceptance
criteria and existing inline discussions. Runtime defects received behavioral
regressions observed failing before implementation. The diagnostic accounting
check characterizes existing correct behavior and has no production change.
Documentation corrections use the existing strict validators.

## Review inventory

| Pull requests | Surface | Findings and disposition |
|---|---|---|
| #37 | Canonical encoding | Preserve order inside nested arrays when only the enclosing collection is a declared set. |
| #38–#43 | Typed measurements, envelopes, profiles, selections, inventories and attribution | Accept ordinary JSON array/object discriminator values in canonical primitives (#39); other reviewed changes had no confirmed defect. |
| #44 | Collection segments | Compare segment and gap boundaries without discarding sub-microsecond precision. |
| #45–#50 | Diagnostics, prices, scenarios, policies, corpora and receipts | No confirmed defect in the reviewed changes. |
| #51 | Self-contained projections | Verify the proven-empty projection correction already present downstream. |
| #52 | Current-run snapshots | Bind diagnostic measurements to the owner; preserve valid scope-free quarantine records and their source bindings. |
| #53 | Producer contract export | No confirmed defect in the reviewed changes. |
| #54 | Counter normalization | Propagate contradictory cache-write evidence; respect verified supersession and final snapshots; preserve price inputs across response groups. |
| #55 | Diagnostic registry | Add integrated coverage proving diagnostics and replay preserve paid identities, totals, coverage and exact cost. |
| #56 | Bounded source reads | No confirmed defect in the reviewed changes. |
| #57 | Selected source normalization | Deduplicate repeated observations and evidence while retaining distinct source declarations, valid siblings and quarantine. |
| #58 | Stream output | Require complete writes or a sanitized failure for normalization, analysis, status and owner delivery. |
| #59 | Publication and lifecycle projection | Reject malformed explicit cost scalars before any lifecycle state changes. |
| #60 | Resolution and pricing | Keep matching raw response identifiers in separate provider accounts distinct in accounting and coverage. |
| #61 | Reports and exports | Preserve exact outcome ratios and export identifiers permitted by the input contracts; share the stream-output correction with #58. |
| #62 | Warnings and delivery | Preserve immutable owner part manifests and distinguish hypothetical repricing from factual spend warnings. |
| #63 | Recovery guidance and integration | Restore complete validation metadata and the exact historical identity inventory; retain the complete repository knowledge records. |

Independent rechecks caught three regressions during repair: scope-free quarantine
compatibility, verified counter supersession, and a local variable shadowing price
inputs. Each received its own regression and correction before proceeding.
The stream recheck also exposed a buffered interpreter-shutdown failure; an
additional real-pipe regression now requires the sanitized exit and diagnostic.

## Verification

Full combined source validation at `524367a446c2456ac2c81ddfa143cd2da47bd51e`:
619 checks passed, zero failed, and two optional private-pattern hygiene checks
were skipped because their local configuration was unavailable. Every required
correction received an independent recheck; no finding is deferred.

Completion records were then reconciled without changing implementation or test
files. Final task validation passed 22 checks with zero failures or skips. The
unchanged strict identity validator passed again and confirmed retained knowledge
tracking. Bash syntax passed for all 17 tracked shell files; ShellCheck was
unavailable. New changes pass the whitespace check. The historical patch and its
intentional context whitespace remain byte-for-byte unchanged.

Integration uses merge commits in dependency order with pinned expected heads.
The resulting main tree must match the validated integration tree exactly.

The complete check is `bash scripts/validate-contracts.sh`. Additional checks cover
the task artifact contract and Bash syntax. Test fixtures use disposable roots,
explicit source selections and synthetic evidence; validation does not deploy
settings, invoke paid models or read historical telemetry implicitly.

## Operational limits

The only built-in reviewed source profile is synthetic. An independent signing
authority remains an external deployment requirement. A valid receipt proves
publication, not source truth or completeness. Missing inventory, unresolved
ownership, unsupported prices and incomplete counters retain explicit unknown or
partial results.

The inventory format identifies expected responses by raw identifier. When those
identifiers collide across provider accounts, observed token and cost contributions
remain distinct, while the coverage denominator remains unknown.

Report publication and warning delivery require operator-protected directories.
Shared warning state assumes one authorized cooperative writer; advisory locks
cannot protect against arbitrary same-user writes. Offline fixtures demonstrate
the implemented contracts, without establishing live provider integration or
model compliance. Private hygiene scans require a separately configured local
pattern file.
