# Execution contract

The execution contract keeps a long-running stage honest about what it observed, published, and completed. It is a reusable pattern, not a domain-specific pipeline implementation.

The reference implementation is in `harness_contracts.execution` and uses only the Python standard library.

## Run layout

Create a fresh run directory with `create_run_root(parent)`. The helper allocates a unique directory and never reuses an existing path. Put temporary and published outputs below that directory; do not publish directly over an older run.

## Inputs

Use `capture_input(path, label=...)` before a stage and `verify_input(record, path)` immediately before publication. The record retains a before/after size and SHA-256 snapshot. A stage may be reported as `complete` only when every required input has an after snapshot and the snapshots match.

## Artifacts

Use `describe_artifact(run_root, relative_path)` only for a regular file inside the run root. It rejects absolute and escaping paths, symlink components, and hard-linked files, then hashes the file. Call `verify_artifact(record, run_root)` immediately before publication or handoff so a post-processing mutation becomes a contract failure.

Artifact records contain a relative path, byte size, SHA-256 digest, and commit flag. The relative path is the stable provenance reference; callers can add the run identifier and source input records around it.

## External commands

Use `run_external(argv, timeout_seconds=...)` with an argument list and `shell=False`. The result captures stdout, stderr, exit status, duration, and whether the command timed out. A timed-out or non-zero command is evidence for `partial` or `failed`, never `complete`.

## Optional capabilities

Use `run_optional_stage(...)` to gate an optional decoder, renderer, accelerator, or provider. Missing capability returns an explicit `partial` result with a reason; it must not fail an unrelated workflow during global dependency preflight. A capability action can raise `OptionalCapabilityUnavailable` to produce the same scoped result.

## Stage result

`StageResult` separates `complete`, `partial`, and `failed`, and can carry input records, artifact records, command diagnostics, and `Provenance`. `to_dict()` produces a compact JSON-compatible record. It refuses to serialize a complete result with unverified or mutated inputs or with a failed command.

Example shape:

```json
{
  "stage": "render",
  "outcome": "partial",
  "inputs": [],
  "artifacts": [],
  "provenance": {
    "tool": "renderer",
    "runtime": "container-image@sha256:...",
    "configuration": {"quality": "preview"},
    "dependencies": {"optional_decoder": "unavailable"}
  },
  "command": null,
  "diagnostics": ["optional decoder is not installed"],
  "reason": "optional capability unavailable"
}
```

Do not convert `partial` or `failed` into success merely because another stage passed.
