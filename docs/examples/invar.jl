# # Riemann Invariant Simplification (Invar)
#
# This tutorial covers the use of the `Invar` module for simplifying scalar
# polynomial invariants of the Riemann tensor. This is essential for proving
# the equivalence of different spacetime metrics.

# ## 1. Setup
# We'll need a manifold and a metric to work with.

# **Julia**
using xAct
reset_state!()
def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f, :g, :h])
def_metric!(-1, "g[-a,-b]", :CD)

# **Python**
# ```python
# from xact.xcore import get_julia
# jl = get_julia()
# jl.xAct.reset_state_b()
# jl.xAct.def_manifold_b("M", 4, ["a", "b", "c", "d", "e", "f", "g", "h"])
# jl.xAct.def_metric_b(-1, "g[-a,-b]", "CD")
# ```

# ## 2. RiemannToPerm
# The core of the `Invar` pipeline is converting tensor expressions into a
# canonical permutation representation.

# **Julia**
expr = "RiemannCD[-a, -b, b, a]"
res = RiemannToPerm(expr, :CD)
# RiemannToPerm may return a single RPerm or a vector of (coeff, RPerm)
rperm = res isa RPerm ? res : res[1][2]
println("Permutation form: ", rperm.perm)

# **Python**
# ```python
# rperm = jl.xAct.RiemannToPerm("RiemannCD[-a, -b, b, a]", "CD")
# print(f"Permutation: {rperm.perm}")
# ```

# ## 3. Loading the Invar Database
# `RiemannSimplify` requires the pre-computed Invar database. The database
# ships with Wolfram xAct and must be available at `resources/xAct/Invar/`.

invar_db_dir = joinpath(@__DIR__, "..", "..", "resources", "xAct", "Invar")
_has_invar_db = isdir(invar_db_dir) && isdir(joinpath(invar_db_dir, "Riemann"))

if _has_invar_db
    LoadInvarDB(invar_db_dir)
    println("Invar database loaded")
else
    @warn "Invar database not found at $invar_db_dir — skipping RiemannSimplify examples"
end

# ## 4. RiemannSimplify
# `RiemannSimplify` is the high-level entry point for simplifying Riemann
# invariants. It uses a pre-computed database of multi-term identities.

# **Julia**
# Consider the Kretschmann scalar. Different dummy index labelings should
# simplify to the same canonical form.
if _has_invar_db #hide
    expr1 = "RiemannCD[-a,-b,-c,-d] RiemannCD[a,b,c,d]"
    expr2 = "RiemannCD[-c,-d,-a,-b] RiemannCD[c,d,a,b]"
    diff = "$expr1 - $expr2"

    result = RiemannSimplify(diff, :CD)
    println("Difference simplified: ", result)  # "0"
end #hide

# **Python**
# ```python
# diff = "RiemannCD[-a,-b,-c,-d] RiemannCD[a,b,c,d] - RiemannCD[-c,-d,-a,-b] RiemannCD[c,d,a,b]"
# result = jl.xAct.RiemannSimplify(diff, "CD")
# print(f"Result: {result}")
# ```

# **Wolfram (xAct)**
# ```wolfram
# RiemannSimplify[RiemannCD[-a,-b,-c,-d] RiemannCD[a,b,c,d] - RiemannCD[-c,-d,-a,-b] RiemannCD[c,d,a,b], CD]
# (* returns 0 *)
# ```

# ## 5. Simplification Levels
# You can control the depth of simplification using the `level` parameter:
# 1. Identity only
# 2. Monoterm (cyclic)
# 3. Bianchi identities
# 4. Covariant derivative commutation
# 5. Dimension-dependent identities
# 6. Dual invariants (4D only)

# **Julia**
if _has_invar_db #hide
    expr = "2 RiemannCD[-a,-b,-c,-d] RiemannCD[a,c,b,d] + RiemannCD[-a,-b,-c,-d] RiemannCD[a,b,c,d]"
    # Level 2 (Cyclic)
    s2 = RiemannSimplify(expr, :CD; level=2)
    println("Level 2: ", s2)

    # Level 3 (Bianchi)
    s3 = RiemannSimplify(expr, :CD; level=3)
    println("Level 3: ", s3)
end #hide

# ## 6. Dual Invariants (4D)
# In 4 dimensions, we can simplify invariants involving the Levi-Civita
# epsilon tensor (represented as `DualRiemann` in Wolfram, or via
# `n_epsilon=1` cases in `Invar`).

# **Julia**
# Dual invariants are only supported if dim=4.
if _has_invar_db #hide
    result = RiemannSimplify("RiemannCD[-a, -b, b, a]", :CD; level=6, dim=4)
    println("Level 6 (4D) result: ", result)
end #hide

# ## 7. Summary
# The `Invar` module provides:
# - `RiemannToPerm`: Tensor string → Canonical Permutation
# - `PermToRiemann`: Canonical Permutation → Tensor string
# - `RiemannSimplify`: End-to-end multi-term simplification
# - `InvSimplify`: Low-level simplification of invariant lists
