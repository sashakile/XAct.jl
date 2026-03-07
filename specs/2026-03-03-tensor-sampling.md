# Spec: Tensor Component Sampling (Tier 3)

**Date:** 2026-03-03
**Status:** Proposed
**Priority:** Medium (Mathematical Rigor)

## Problem Statement

Tier 2 comparison (`Simplify[lhs - rhs] == 0`) is powerful but can be extremely slow for complex tensor identities or may fail if the CAS's simplification rules are incomplete. Tier 3 currently only supports scalar variables, leaving a gap for verifying tensor-valued expressions with free indices.

## Proposed Solution: Numeric Tensor Realization

Implement a numeric validation layer that treats tensor expressions as multi-dimensional arrays (tensors in the computational sense) and verifies identities via random component assignment.

### 1. Random Component Generation
- **Manifolds:** For each unique `Manifold`, define a fixed dimension $N$.
- **Metrics:** Generate random metrics that are **well-conditioned** (e.g., $g = A A^T + \epsilon I$ for Euclidean or signature-adjusted variants) to prevent numerical blow-up during inverse calculations.
- **Tensors:** Generate random $N \times N \times \dots$ arrays of floats **or complex numbers** (if the test type is `Spinors` or complex-valued geometry).
- **Symmetries:** Honor symmetry constraints (Symmetric/Antisymmetric) by projecting the random array onto the appropriate symmetry subspace after generation.

### 2. Numeric Evaluation Pipeline
- **Mapping:** Map the symbolic expression to a numeric equivalent (e.g., using `numpy.einsum`).
- **Contraction:** Perform all index contractions numerically, treating the result as a component array.
- **Comparison:** If the identity $A = B$ holds, the difference array $A - B$ should satisfy `np.allclose(diff, 0, atol=1e-10)`.

### 3. Integration with `sampling.py`
- Modify `_extract_variables` to also identify `Tensors` and their `Manifolds`.
- Fetch manifold dimensions and signatures from the `TestAdapter` context.

## Interdependencies
- **Context Awareness:** Depends on **Stateful Cleanup** (`specs/2026-03-03-stateful-cleanup.md`) to correctly identify the current manifold properties from the active session.

## Success Criteria
- Correctly identifies equivalence for the First Bianchi Identity `R[a,b,c,d] + R[a,c,d,b] + R[a,d,b,c] == 0` without using `Simplify`.
- Provides a "confidence score" based on 5+ random numeric realizations.
- Handles tensors of rank up to 4 in a 4D manifold.
