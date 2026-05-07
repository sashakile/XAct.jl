# XTensor Extensions Design: xCoba, xPert, xTras

**Date:** 2026-03-26
**Status:** Implemented
**Location:** `src/XTensor.jl` (all three subsystems live within this module)

---

## 1. xCoba — Coordinate Basis Framework

### 1.1 Purpose

Bridge between abstract-index tensor algebra and numerical component representations.
Provides basis definitions, coordinate charts, basis changes, and component tensor arrays.

### 1.2 Types

```julia
struct BasisObj
    name::Symbol              # e.g. :tetrad
    vbundle::Symbol           # e.g. :TangentM
    cnumbers::Vector{Int}     # integer labels for basis elements
    parallel_deriv::Symbol    # auto-created parallel derivative (PDname)
    is_chart::Bool            # true if created by def_chart!
end

struct ChartObj
    name::Symbol              # e.g. :Schw
    manifold::Symbol
    cnumbers::Vector{Int}
    scalars::Vector{Symbol}   # coordinate fields (e.g. [:t, :r, :theta, :phi])
end

struct BasisChangeObj{T<:Number}
    from_basis::Symbol
    to_basis::Symbol
    matrix::Matrix{T}         # transformation (n x n)
    inverse::Matrix{T}
    jacobian::T               # determinant (cached)
end

struct CTensorObj{T<:Number,N}
    tensor::Symbol
    array::Array{T,N}         # numerical components
    bases::Vector{Symbol}     # basis label per slot
    weight::Int               # density weight
end
```

### 1.3 Key Design Decisions

- `def_chart!` creates both a ChartObj AND a BasisObj (coordinate basis), plus registers
  coordinate scalars as rank-0 tensors.
- Non-coordinate bases auto-create a parallel derivative operator.
- `set_basis_change!` stores both forward and inverse directions; validates invertibility.
- `ToBasis` / `FromBasis` bridge abstract and component representations.
- `Christoffel` computes connection coefficients from metric components + derivatives.

### 1.4 Test Coverage

35 Christoffel tests + xCoba coverage within the 567 XTensor tests.

---

## 2. xPert — Perturbation Theory

### 2.1 Purpose

Support metric and tensor perturbation expansions for linearized gravity and
higher-order perturbation theory.

### 2.2 Type

```julia
struct PerturbationObj
    name::Symbol        # e.g. :Pertg1
    background::Symbol  # e.g. :g
    order::Int          # perturbation order >= 1
end
```

### 2.3 Key Functions

| Function | Purpose |
|----------|---------|
| `def_perturbation!(tensor, background, order)` | Register a perturbation |
| `perturb(expr, order)` | Apply multinomial Leibniz rule to expression |
| `PerturbationOrder(tensor)` | Query registered order |
| `PerturbationAtOrder(background, order)` | Lookup perturbation by background + order |
| `perturb_curvature(metric, order)` | Perturbation rules for curvature tensors |

### 2.4 Design Decisions

- Registry-based: perturbations looked up by (background, order) pair.
- Leibniz rule: `delta^n(A * B * ...) = sum_{compositions} C(n; i1,...,ik) * delta^i1(A) * ... * delta^ik(B)`.
- Factors without registered perturbations are treated as background (variation = 0).

---

## 3. xTras — Extended Utilities

### 3.1 Purpose

Higher-level tensor manipulation utilities: integration by parts, variational
derivatives, tensor collection, contractions, symmetry detection, trace-free projection.

### 3.2 Key Functions

| Function | Purpose |
|----------|---------|
| `IBP(expr, covd)` | Integration by parts; drops pure divergences |
| `TotalDerivativeQ(expr, covd)` | True iff expression is a total derivative |
| `VarD(expr, field, covd)` | Euler-Lagrange variational derivative |
| `CollectTensors(expr)` | Collect like tensor terms (delegates to ToCanonical) |
| `AllContractions(expr, metric)` | Enumerate all independent scalar contractions |
| `SymmetryOf(expr)` | Detect symmetry by index permutation behavior |
| `MakeTraceFree(expr, metric)` | Trace-free projection for rank-2 tensors |

### 3.3 Design Decisions

- `IBP`: term-by-term Leibniz factorization, extracts CovD, drops pure divergences.
- `VarD`: composes Leibniz expansion + IBP to compute functional derivatives.
- `AllContractions`: generates perfect matchings of free indices; deduplicates via Simplify.
- `MakeTraceFree`: subtracts `(1/dim) * g_{ab} * g^{cd} * T_{cd}` from rank-2 tensors.

### 3.4 Test Coverage

19 xTras tests within `test/julia/test_xtensor.jl`.
