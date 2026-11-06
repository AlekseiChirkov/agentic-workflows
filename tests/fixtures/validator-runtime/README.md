# Maintaining the nested source guard

The exception manifest records reviewed call sites and, where necessary, exact
source dependencies. An inventory fingerprint binds some classifications to all
regular shell and Python files under `tests` and to the validator. A source change
can therefore invalidate classifications even when the changed file has no new
nested call. This is intentional: the fingerprint alone is not approval.

When updating the guard:

1. Review the complete source diff and run the guard. Inspect each new diagnostic
   and each changed call site, its arguments, executable, generated content and
   dependencies. Reject unresolved execution paths. Add or change only the exact
   reviewed records; do not generate a blanket allowlist from diagnostics.
2. Finish all shell and Python changes before computing the inventory fingerprint.
   Load `source_guard.py` with Python bytecode disabled and call
   `_inventory_digest(root, inventory_sources(root))`. The helper normalizes the
   manifest hash embedded in the guard to avoid a circular digest. Update existing
   `inventory_sha256` fields only after reviewing their changed source inputs.
3. For each changed classified context or dependency, recompute its exact context,
   statement count or dependency digest after review. Preserve unaffected entries
   and reasons; remove records only when their call sites were removed.
4. Serialize the manifest, calculate its SHA-256 over its exact bytes, and update
   the manifest digest in `source_guard.py`. Do not change shell or Python source
   afterward without repeating the inventory check.
5. Run the guard, its regression and external-source suites, and the inventory
   oracle. Confirm that they pass and inspect the final diff, including all added,
   removed and modified exceptions. These checks do not substitute for review.
