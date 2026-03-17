# Getting Started with xAct.jl

This guide covers quick start usage for Julia and Python, and provides a Wolfram-to-Julia migration reference.

!!! info "Prerequisites"
    Ensure you have installed `xAct.jl` according to the [Installation Guide](installation.md) before starting this tutorial.

---

## 1. Quick Start (Julia)

The primary interface for tensor calculus in Julia is the REPL or a Jupyter notebook.
We recommend using the **typed API** for better validation and standard Julia syntax.

```julia
using xAct

reset_state!()
M = def_manifold!(:M, 4, [:a, :b, :c, :d])
def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")

@indices M a b c d       # declare typed index variables
T_h = tensor(:T)         # look up registered tensor handle

# T is symmetric — T_{ba} - T_{ab} = 0
ToCanonical(T_h[-b,-a] - T_h[-a,-b])   # "0"
```

> **String API:** `ToCanonical("T[-b,-a] - T[-a,-b]")` is equivalent and still works everywhere.

For a more detailed walkthrough, see the [Basics Tutorial](examples/basics.md).

### With a Metric

Defining a metric automatically creates the associated curvature tensors (Riemann, Ricci, Weyl, etc.).

```julia
g = def_metric!(-1, "g[-a,-b]", :CD)   # creates Riemann, Ricci, Weyl, ...
@indices M a b c d e f
Riem = tensor(:RiemannCD)

# First Bianchi identity
ToCanonical(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c])   # "0"
```

---

## 2. Quick Start (Python)

The `xact` Python package provides a snake-case API that wraps the Julia core.

```python
import xact

xact.reset()
M = xact.Manifold("M", 4, ["a", "b", "c", "d"])
T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")

a, b, c, d = xact.indices(M)    # typed index objects
T_h = xact.tensor("T")          # tensor handle

xact.canonicalize(T_h[-b,-a] - T_h[-a,-b])   # "0"
```

For a full walkthrough, see the [Python notebook](https://github.com/sashakile/sxAct/blob/main/notebooks/python/basics.ipynb).

---

## 3. Reference: Migration Rosetta Stone

For experienced `xAct` users, this table shows the direct mappings from Wolfram Language to Julia.

| Operation | Wolfram (xAct) | Julia (xAct.jl) | Status |
| :--- | :--- | :--- | :--- |
| **DefManifold** | `DefManifold[M, 4, {a,b}]` | `def_manifold!(:M, 4, [:a, :b])` | ✅ Verified |
| **DefTensor** | `DefTensor[T[-a,-b], M]` | `def_tensor!(:T, ["-a", "-b"], :M)` | ✅ Verified |
| **DefMetric** | `DefMetric[-1, g[-a,-b], CD]` | `def_metric!(-1, "g[-a,-b]", :CD)` | ✅ Verified |
| **ToCanonical** | `ToCanonical[expr]` | `ToCanonical(expr)` | ✅ Verified |
| **Contract** | `ContractMetric[expr]` | `Contract(expr)` | ✅ Verified |
| **Simplify** | `Simplification[expr]` | `Simplify(expr)` | ✅ Verified |
| **RiemannSimplify** | `RiemannSimplify[expr, CD]` | `RiemannSimplify(expr, :CD)` | ✅ Verified |
| **RiemannToPerm** | `RiemannToPerm[expr]` | `RiemannToPerm(expr)` | ✅ Verified |
| **CommuteCovDs** | `SortCovDs[expr]` | `CommuteCovDs(expr)` | ✅ Verified |
| **IBP** | `IBP[expr, v]` | `IBP(expr, :CD)` | ✅ Verified |
| **VarD** | `VarD[field][CD]expr` | `VarD(expr, :field, :CD)` | ✅ Verified |
| **Perturb** | `Perturbation[expr]` | `Perturb(expr)` | ✅ Verified |

---

## Next Steps

- **Core Concepts**: See [Key Concepts](concepts.md) for details on the symbol registry and TExpr layer.
- **Migrating from Wolfram?**: See the [Wolfram Migration Guide](wolfram-migration.md) for the expression translator and REPL.
- **Verification**: Learn how we ensure mathematical correctness in the [Verification Framework Guide](verification-tools.md).
- **Status Dashboard**: Check the [Feature Matrix](theory/STATUS.md) to see which functions are ready for production use.
