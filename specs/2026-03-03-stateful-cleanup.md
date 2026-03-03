# Spec: Stateful Oracle Cleanup

**Date:** 2026-03-03
**Status:** Proposed
**Priority:** Medium (Stability)

## Problem Statement

Wolfram/xAct is inherently stateful. Defining a manifold or tensor in one test file adds symbols to the global environment and internal `xAct` registries (e.g., `Manifolds`, `Tensors`). 
- **Pollution:** Definitions from `test_a.py` can cause "Symbol protected" or "Already defined" errors in `test_b.py`.
- **Memory:** Long-running test sessions can lead to kernel memory exhaustion as definitions accumulate.
- **Nondeterminism:** Test success may depend on the order in which files are executed.

## Proposed Solution: Registry-Aware Teardown

Implement a rigorous cleanup protocol that restores the Wolfram kernel to a "pristine" state between `TestAdapter` contexts.

### 1. Enhanced `teardown()`
The `WolframAdapter.teardown()` method must execute a cleanup script that targets `xAct` internals while **protecting infrastructure symbols**:
- All `sxAct` infrastructure functions and communication variables must be moved to a dedicated `sxAct`Context`` that is **never** cleared.
- Cleanup script for the `Global` context:
```wolfram
(* Cleanup script *)
Unprotect["Global`*"];
ClearAll["Global`*"];
Remove["Global`*"];

(* Prune xAct Internal Lists *)
Manifolds = {};
Tensors = {};
DefaultMetric = None;
```

### 2. Context Verification (Source of Truth)
Modify `WolframAdapter.initialize()` to perform a "leak check" **before** every test file:
- Query `Length[Tensors]` and `Length[Manifolds]`.
- If non-zero, the kernel is considered "dirty" (likely due to a previous crash during teardown).
- **Mandatory Action:** Force-restart the kernel via the `KernelManager` to ensure absolute isolation.

### 3. Isolation Enforcement
- Use `Begin["context_id`"]` and `End[]` aggressively for all evaluations.
- Ensure the `KernelManager` communication layer is resilient to `Global` context clears.

## Interdependencies
- **Numeric Validation:** This spec is a prerequisite for **Tensor Component Sampling** (`specs/2026-03-03-tensor-sampling.md`) to ensure manifold definitions don't collide during random realization.

## Success Criteria
- Running the same test file twice in the same session does not produce "Symbol already defined" errors.
- `Length[Tensors]` returns `0` at the start of every new test file.
- `KernelManager.restart()` is only called as a fallback, minimizing execution time.
