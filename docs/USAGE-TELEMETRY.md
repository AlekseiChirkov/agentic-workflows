# Offline usage normalization

The offline normalizer reads only the ordinary files explicitly listed in a source selection. It never searches for other exports or publishes to the shared usage store. Invoke it with:

```sh
USAGE_TELEMETRY_CONFIG=/absolute/private/config.json \
  python3 scripts/usage-telemetry.py normalize \
  --profile PROFILE_ID --input-manifest /absolute/selection.json | trusted-consumer
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

The manifest declares source paths, digests, observation time, attribution and all required byte and record limits. The helper verifies the profile, scope and limits before opening source files. Invalid containers produce no bundle; invalid individual records are omitted and recorded as sanitized partial diagnostics. The complete canonical bundle is emitted to standard output only after validation and normalization. Standard output must be a pipe or socket; file and terminal output are rejected. The former `--output FILE` interface is no longer supported. Errors intentionally omit local paths and payloads.

The helper does not create output files. The receiving process is responsible for preserving the bundle and for any atomic installation; it must keep its output outside the shared usage store. Only the logging producer may publish there. This boundary does not prevent a caller or receiving process from independently writing or redirecting data into the store. A shell may create or truncate a redirected file before the helper starts, so do not redirect standard output directly to a file. A broken pipe can leave the receiver with partial bytes; consumers must check the helper's exit status and validate the complete bundle before using it.
