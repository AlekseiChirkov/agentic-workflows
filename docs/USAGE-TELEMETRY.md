# Offline usage normalization

The offline normalizer reads only the ordinary files explicitly listed in a source selection. It never searches for other exports or publishes to the shared usage store. Invoke it with:

```sh
USAGE_TELEMETRY_CONFIG=/absolute/private/config.json \
  python3 scripts/usage-telemetry.py normalize \
  --profile PROFILE_ID --input-manifest /absolute/selection.json \
  --output /absolute/private/bundle.json
```

The configuration is an explicit operator trust decision. It must be a regular file owned by the current user with mode `0600`, accessed without symlinks. Keep it and its parent directories private. It has this structure:

```json
{
  "schema_version": 1,
  "profiles": [{"profile": {}, "sha256": "PROFILE_CANONICAL_SHA256"}],
  "owner_scope": {"owner_kind": "task", "owner_id": "sha256:OPAQUE_OWNER_ID"},
  "project_identifier": "PRIVATE_PROJECT_IDENTIFIER",
  "provider_identifier": "PRIVATE_PROVIDER_IDENTIFIER",
  "run_id": "RUN_ID",
  "key_hex": "PRIVATE_HEX_KEY"
}
```

Replace `profile` with a complete validated source profile and its digest with the lowercase SHA-256 of its canonical JSON bytes. The helper also requires that digest to appear in its built-in reviewed public-profile list. The initial list contains only the public synthetic test format; other formats require an explicit review of every serialized profile field and its semantics before their digest is added. The configured profile ID and version must match the selection; ambiguous IDs and mismatched digests are rejected. The operator must independently establish the profile's provenance and applicability before trusting it: a matching digest establishes consistency, not authenticity. Likewise, matching the configured owner scope authorizes the selection but does not prove attribution. Set `key_hex` to at least 32 randomly generated secret bytes encoded as lowercase hex. Store the key locally and never place it, the configuration, or the input selection in the shared usage store. Reusing the same key gives stable domain-separated opaque identifiers; changing it changes those identifiers.

Set `run_id` to the existing lifecycle run identifier: exactly eight lowercase hexadecimal characters. The helper does not verify that this identifier proves ownership or that the run exists.

The manifest declares source paths, digests, observation time, attribution and all required byte and record limits. The helper verifies the profile, scope and limits before opening source files. Invalid containers produce no output; invalid individual records are omitted and recorded as sanitized partial diagnostics. The output is a self-contained usage bundle and must be outside `ORCHESTRAIL_LOG_ROOT/usage/v1` (or `logs/usage/v1` if unset). Only the logging producer can publish to shared storage. Errors intentionally omit local paths and payloads.

Use an output directory whose location and all parent directories are controlled by the operator for the entire command. Do not run concurrent processes that can rename that directory or move it into the shared store. The helper rejects symlinked destinations and detects a directory moved before its checks, failing closed when its current location cannot be verified through `/proc/self/fd`. These checks cannot prevent a concurrent rename between a check and a filesystem operation; ordinary permissions do not isolate mutually untrusted processes running under the same user ID. An environment with such processes needs separate operating-system isolation before using this command.

## Publishing authorized bundles

Publication requires an independent authority. The bundle author and the local configuration key cannot authorize the bundle themselves. This repository verifies permits but does not supply or deploy the external authority that reviews sources and issues them. Without that authority, publication fails closed and returns no acceptance receipt. The existing lifecycle logger continues to exit successfully when publication is unavailable.

An administrator must install the authority's Ed25519 public key in PEM format under `/etc/orchestrail/usage-authorities/`, with a filename ending in `.pem`. The file and every directory from `/` must be owned by root and must not be writable by the group or others; symbolic links are rejected. Keep the signing key outside the bundle author's control. A root-owned public key outside this registry is not an authority registration.

Set `USAGE_TELEMETRY_AUTHORITY_KEY` to the registered public-key path before `run-start`. The producer records its fingerprint for that run. The active run's project must match `project_identifier` in the private configuration; the configuration and bundle must name the same run. For a run-scoped owner, `owner_id` is the domain-separated keyed identifier derived from the registered run ID. A different key, run, owner, project, profile or bundle is rejected. Only active runs are currently eligible; a closed run has no active registration and is rejected.

The independent authority must verify the selected sources and the normalized bundle before it signs a permit. It signs the following canonical JSON object, excluding the `signature` field, prefixed with the bytes `orchestrail:usage-authority:v1` followed by one NUL byte:

```json
{
  "schema_version": 1,
  "kind": "usage_authority_permit",
  "bundle_sha256": "CANONICAL_BUNDLE_SHA256",
  "profile_id": "PROFILE_ID",
  "profile_version": "PROFILE_VERSION",
  "run_id": "RUN_ID",
  "scope": {"owner_kind": "run", "owner_id": "sha256:OPAQUE_OWNER_ID"}
}
```

Add the Ed25519 signature as a lowercase hexadecimal `signature` field and save the resulting permit in an explicitly selected, current-user-owned `0600` file. The permit contains no source paths or raw source content. A signature verifies the authority's approval of this exact bundle and scope; it is not a substitute for the authority's independent source verification.

Create the normalizer's separate local provenance file using `--provenance-output`. Its MAC checks consistency with the local configuration, but cannot by itself establish independent provenance. With the registered key and a separately issued permit, invoke publication as follows:

```sh
ORCHESTRAIL_USAGE_MODE=on \
USAGE_TELEMETRY_CONFIG=/absolute/private/config.json \
USAGE_TELEMETRY_PROVENANCE=/absolute/private/provenance.json \
USAGE_TELEMETRY_AUTHORITY_KEY=/etc/orchestrail/usage-authorities/authority.pem \
USAGE_TELEMETRY_AUTHORITY_PERMIT=/absolute/private/permit.json \
  bash scripts/log-step.sh usage-ingest --manifest /absolute/private/bundle.json
```

The verifier needs the optional Python `cryptography` package with Ed25519 support. Missing dependencies, an unregistered key, invalid permissions, a missing permit or an invalid signature produce no receipt and no publication. Publication does not reread the selected source files or search the run history.
