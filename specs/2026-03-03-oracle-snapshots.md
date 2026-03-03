# Spec: Oracle Snapshots & CI Harness

**Date:** 2026-03-03
**Status:** Proposed
**Priority:** High (RSE / Infrastructure)

## Problem Statement

The `sxAct` integration tests currently require a live, licensed Wolfram Engine with `xAct` installed. This creates several bottlenecks:
1. **CI/CD Limitations:** Standard CI environments (GitHub Actions) cannot run these tests due to licensing and setup complexity.
2. **Contributor Friction:** New contributors without a Wolfram license cannot verify their changes against the "ground truth."
3. **Execution Speed:** `xAct` initialization and evaluation via Docker are slow (~3+ minutes for full load).

## Proposed Solution: The Snapshot Pattern

Implement a "Record/Replay" mechanism via a `SnapshotMiddleware` that wraps the `OracleClient`. This allows the test suite to run in "Snapshot Mode," using pre-recorded JSON results instead of calling a live kernel.

### 1. Snapshot Storage Structure
Store snapshots in `tests/snapshots/` organized by test module:
```
tests/snapshots/
├── integration/
│   ├── test_xact_basics/
│   │   ├── define_manifold_001.json
│   │   └── symmetric_tensor_002.json
```

### 2. Snapshot JSON Schema
```json
{
  "request": {
    "action": "DefTensor",
    "args": { "name": "T", "indices": ["-a", "-b"] },
    "context_id": "uuid-123",
    "xact_version": "1.2.0"
  },
  "response": {
    "status": "ok",
    "repr": "T[-a, -b]",
    "normalized": "T[-$1, -$2]",
    "properties": { "rank": 2, "manifold": "M" }
  },
  "hash": "sha256:..."
}
```

### 3. Implementation Plan
- **`SnapshotMiddleware`:** 
    - Acts as a proxy between the `TestAdapter` and `OracleClient`.
    - Computes a unique key for each request as `sha256(json_serialize(request_args, sort_keys=True))`.
    - Handles multiple evaluations per test file by indexing snapshots by their request hash.
- **CLI Flags:**
    - `--oracle-mode=live`: Default, uses the Docker oracle.
    - `--oracle-mode=record`: Executes live and saves new/changed results to disk.
    - `--oracle-mode=replay`: Fails if a snapshot is missing or if `xact_version` in the snapshot differs from the current environment (used in CI).
- **Verification:** Implement a `regen-oracle` command to bulk-refresh snapshots.

## Interdependencies
- **Stable Hashing:** Depends on **AST-Based Normalization** (`specs/2026-03-03-ast-normalization.md`) to ensure the `normalized` field in snapshots remains stable across refactors.

## Success Criteria
- Integration tests pass in an environment (e.g., GitHub Actions) where the Docker oracle is not running.
- `xact-test --oracle-mode=replay` execution time is < 5 seconds for the full suite.
- Replay fails immediately if the recorded `xact_version` drifts from the installed version.
