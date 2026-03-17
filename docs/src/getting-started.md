# Getting Started with xAct.jl

This page covers quick start usage, a Wolfram-to-Julia migration reference, key concepts, and the verification framework.

!!! info "Prerequisites"
    Ensure you have installed `xAct.jl` according to the [Installation Guide](installation.md) before starting this tutorial.

---

## 1. Quick Start

The primary interface for tensor calculus is the Julia REPL or a Jupyter notebook.
Expressions are built with the **typed API** — index objects and operator overloading
that validate slot counts and manifold membership at construction time.

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

### Python Quick Start

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

### With a Metric

```julia
g = def_metric!(-1, "g[-a,-b]", :CD)   # creates Riemann, Ricci, Weyl, ...
@indices M a b c d e f
Riem = tensor(:RiemannCD)

# First Bianchi identity
ToCanonical(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c])   # "0"
```

For the full API reference, see the [Typed Expression API](api-python.md#typed-expression-api) section.

---

## 2. Reference: Migration Rosetta Stone

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

## 3. Key Concepts

- **Symbol Registry**: `xAct.jl` maintains a global registry of manifolds, bundles, and tensors. Functions that modify this state end in `!` (e.g., `def_tensor!`).
- **Indices**: We follow the standard xAct notation: `-a` for covariant (lower) and `a` for contravariant (upper) indices.
- **Parity Verification**: Operations in `xAct.jl` are verified against the original Wolfram implementation through automated snapshot tests using a Dockerized Wolfram Oracle.

## 4. Verification Framework

Every operation in `xAct.jl` is verified against the original Wolfram implementation using a TOML-based test runner. Tests are defined declaratively and checked against oracle snapshots captured from the Wolfram Engine.

To run the verification suite against the Julia backend:

```bash
# Run all xTensor verification tests
uv run xact-test run tests/xtensor/ --adapter julia --oracle-mode snapshot --oracle-dir oracle

# Run a single test file
uv run xact-test run tests/xtensor/canonicalization.toml --adapter julia --oracle-mode snapshot --oracle-dir oracle
```

See the [Developer/Verification Install](installation.md#3-developerverification-install) section for setup instructions.

## Next Steps

- **Migrating from Wolfram?** See the [Wolfram Migration Guide](wolfram-migration.md) for the expression translator and REPL.
- **Installation**: See the [Installation Guide](installation.md) for local setup.
- **Status Dashboard**: Check the [Feature Matrix](theory/STATUS.md) to see which functions are ready for production use.
