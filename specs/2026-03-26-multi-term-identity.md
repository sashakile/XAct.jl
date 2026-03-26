# Multi-Term Identity Framework Design

**Date:** 2026-03-26
**Status:** Implemented
**Location:** `src/XTensor.jl` (struct at lines 217-251, application at lines 539-679)

---

## 1. Problem

Tensor algebra requires multi-term identities (e.g., Bianchi identity for Riemann)
to reduce expressions to a canonical form. The original implementation used a hardcoded
`_bianchi_reduce!` function specific to the Riemann tensor, which could not be extended
to user-defined identities.

## 2. Design

### 2.1 MultiTermIdentity Struct

```julia
struct MultiTermIdentity
    name::Symbol                        # e.g. :FirstBianchi
    tensor::Symbol                      # which tensor (e.g. :RiemannCD)
    n_slots::Int                        # tensor rank (4 for Riemann)
    fixed_slots::Vector{Int}            # slot positions held constant
    cycled_slots::Vector{Int}           # slot positions permuted across terms
    slot_perms::Vector{Vector{Int}}     # rank-permutation for each term
    coefficients::Vector{Rational{Int}} # coefficient per term (sum = 0)
    eliminate::Int                      # which term index to eliminate
end
```

The identity encodes: `sum_i coefficients[i] * T[slot_perms[i]] = 0`, where one
designated term (`eliminate`) is solved in terms of the others.

### 2.2 Registration

```julia
RegisterIdentity!(tensor_name, identity; session)
```

Stores the identity in `session.identity_registry[tensor_name]`. Multiple identities
can be registered per tensor.

### 2.3 Application During Canonicalization

`_apply_identities!(coeff_map, struct_map, key_order)` runs after ToCanonical:

1. Groups canonical terms into **sectors** (same fixed slots + sorted cycled slots).
2. Within each sector, checks if the "eliminate" term is present.
3. If found, rewrites it as a linear combination of the other terms.
4. Updates the coefficient map in-place.

### 2.4 Auto-Registration

When `def_tensor!` creates a tensor with `:RiemannSymmetry` and 4 slots, the framework
auto-calls `_make_bianchi_identity()` to register the first Bianchi identity:
`R_{a[bcd]} = 0`, i.e., `R_{abcd} - R_{abdc} + R_{adbc} = 0`.

## 3. Extensibility

Users can register custom identities for any tensor. The framework is general enough
to handle any multi-term linear relation among permutations of a single tensor's slots.

## 4. Test Coverage

26 MultiTermIdentity tests in `test/julia/test_xtensor.jl` verify auto-Bianchi
registration, manual identity registration, and sector-wise elimination.
