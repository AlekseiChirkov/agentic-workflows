# Hook logging final review and integration

Date: 2026-10-26

## Result

Product PRs #22 through #29 were merged into main in dependency order using merge
commits. Product delivery is integrated at 8184bfe87a4c696e5c100032ebdf0f5fd8af64ee.
Every actual merge tree and its two parents were verified against the predicted
result. The final product tree is 270c243adf8e7a2b1ddbcd0c78a16a16acdea96d.

## Independent reviews

Each original PR had a separate reviewer. Reviewers inspected its complete unique
diff and exercised cumulative behavior at fa865f4363a9f2420984ee3b1249deed2f1fc4ec,
distinguishing defects already fixed later from remaining defects. The producer
repair received a separate independent review and follow-up verification.

| PR | Scope | Executed checks | Result |
|---|---|---|---|
| #22 | Repository tracking policy | 69 assertions, two isolated sync runs | PASS |
| #23 | Correlated producer | 35 focused checks, canonical and independent boundary probes | Findings resolved by #29 |
| #24 | Native adapter | 38 adapter cases, 23 independent probes | PASS |
| #25 | Owned installation | 39 installer cases, two registry cases, eight independent groups | PASS |
| #26 | Workflow coverage | Five acceptance groups, 15 independent scenarios, 45 original assertions retained | PASS |
| #27 | Exact timing | 51 timing groups, two documentation checks, 14 independent probes | PASS |
| #28 | Delivery function structure | Three source checks, 35 producer and 38 adapter cases, actual 91-function Bash AST | PASS |
| #29 | Producer repair | 38 producer, 38 adapter, three source checks; 37 malformed-cache and 40 NUL-route checks | PASS |

These counts describe overlapping scoped suites and are not additive coverage totals.

## Findings and repairs

Three important findings and one advisory regression were repaired:

1. Cached acceptance required raw canonical positive bounded sequences before JSON
   conversion, including one complete fixed-schema object and matching arguments.
2. Ordinary updates widened private metadata permissions. Every metadata replacement
   now remains mode 0600, including temporary files under permissive umasks.
3. Newly accepted arbitrary unrecognized correlated step names skipped the documented
   advisory. The advisory is restored; valid session unknown, replay and rejection
   behavior remain compatible.
4. Independent repair review found that Bash discarded literal NUL before validation.
   Raw metadata now rejects NUL before explicit lookup or line parsing.

Separate regression commits precede both repairs:

- Initial regressions: f8c85c478bfc84f6821d170bc1a3574212b690c5.
- Initial repair: c42a6632e680fddcef6810ff0be95aa857206814.
- NUL regressions: cfa4f6f45c492f1c746559f09b0b0515b4f7bc51.
- Final repair: da4e027b708d42cb6ae858d032c84ceb71b8fd5f.

Original assertions remain intact. Historical mathematical-integer lint compatibility,
ordinary optional-jq logging, literal percent/escaped text, event-file permissions,
receipt ordering and actual append/metadata rollback are preserved. No requirement
was weakened. An optional fixture row-count clarification is not a demonstrated
product defect.

## Complete verification

The fresh complete validator ran in a clean detached checkout at
da4e027b708d42cb6ae858d032c84ceb71b8fd5f after scoped runtime checks finished:

~~~bash
bash scripts/validate-contracts.sh
~~~

Result: **594 passed, 0 failed, 2 optional private-pattern skips; exit zero**.
Validation output SHA-256:
80d4fec0b97daf274ff55b8b2d666322013fcc8f4fbbbfcec251f95fd853587b.
All 125 non-knowledge files were byte-identical in the reviewed publication
snapshot. Subsequent integration bookkeeping changes documentation only.

An earlier incomplete run was superseded after the NUL finding. It is not the
completion evidence above. One existing 12-second bounded-transcript fixture timed
out under CPU contention during scoped checks, then passed unchanged both alone and
in the complete serial adapter rerun. No timeout or assertion was changed. The
complete repository validator above passed without a remaining failure.

## Ancestry and merge verification

The initial specification had already reached main separately. Producer branch
synchronization preserved its complete tree
4f27c0e23ea26106ff1863b8f709d56d3034115a:

- d804b01b2b1cd6e82f1890fee3128ebd0655fd5f has parents original producer head
  6695f37ac3c6c3fe979f47fcdf84eadf6c475962 and original main
  6fbaf42cca979f132280b1b04698d41306331626.
- After #22 merged, GitHub refused the first #23 merge despite a clean local result.
  cd6abdb05d64ac97061cb35c5e08995ff89abe97 has parents d804b01 and actual main
  503f94a16133a7de8999b61a17785135cabbcb08, again with the identical tree.
  Independent review checked the new pin; GitHub then reported it mergeable.

The remaining graph was simulated again. Every successor was retargeted to main
after its predecessor merged. Each merge used the expected head SHA; the fetched
result had the expected complete tree and exact two parents. Published commits and
original branch points remain intact. No force push, rebase, direct main push or
branch deletion was used.

| PR | Merged head | Verified merge commit |
|---|---|---|
| #22 | 9bb1358be2ee9d09f83520239ff30baa29c05906 | 503f94a16133a7de8999b61a17785135cabbcb08 |
| #23 | cd6abdb05d64ac97061cb35c5e08995ff89abe97 | b44514ad58e7a183e518ec6d551e88dcb95e5697 |
| #24 | 30f0819e8800f222a59d44211ec01682fa2bfbda | 17878020da1bdf8937cc85ae6733a4bdf81f155e |
| #25 | 4cf5c515d11b5730090923647e1def2d52129095 | b76f2bf4f2529d2d2e80d9e415c121c95a459009 |
| #26 | 2ad00eda9d4371673c719ea4d40b1c8fdf74f03c | 49f3ec91c68b4d0da672bfb27b1628eadb84a428 |
| #27 | a9936d21f42aaf555dbcd67d70f334a1df38cb51 | 628dc40b8ab511e5893f7d5429a55221c6a1e985 |
| #28 | fa865f4363a9f2420984ee3b1249deed2f1fc4ec | 37eb3b4a20987c41bd97264b0dc570e7d173b14d |
| #29 | 2de5ae3ea31dfa4fbb01b10973fcb68bc46d6362 | 8184bfe87a4c696e5c100032ebdf0f5fd8af64ee |

## Verification limits

Tests used disposable settings, project roots and log stores. No live model
invocation, native event firing, real user-settings deployment or historical-corpus
access is claimed. ShellCheck was unavailable. The two skipped checks require
maintainer-local private patterns. GitHub returned no commit statuses or
pull-request workflow runs for the reviewed heads; local complete validation is
recorded above.
