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

The manifest declares source paths, digests, observation time, attribution and all required byte and record limits. The helper verifies the profile, scope and limits before opening source files. Invalid containers produce no output; invalid individual records are omitted and recorded as sanitized partial diagnostics. The output is a self-contained usage bundle and must be outside `ORCHESTRAIL_LOG_ROOT/usage/v1` (or `logs/usage/v1` if unset). Only the logging producer can publish to shared storage. Errors intentionally omit local paths and payloads.

Use an output directory whose location and all parent directories are controlled by the operator for the entire command. Do not run concurrent processes that can rename that directory or move it into the shared store. The helper rejects symlinked destinations and detects a directory moved before its checks, failing closed when its current location cannot be verified through `/proc/self/fd`. These checks cannot prevent a concurrent rename between a check and a filesystem operation; ordinary permissions do not isolate mutually untrusted processes running under the same user ID. An environment with such processes needs separate operating-system isolation before using this command.
