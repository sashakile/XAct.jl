# # Basics Tutorial
#
# This tutorial walks through a safe Julia-first session in `XAct.jl`.
# You should already have completed [Installation](../installation.md) and skimmed [Getting Started](../getting-started.md).
#
# The goal is to define a manifold, add tensors and a metric, and verify a few core identities with the typed API.
# If you want Python examples or Wolfram translation details, use the linked notebook and migration guides rather than this tutorial.

# ## 1. Start a clean Julia session
# Begin in a fresh session so repeated definitions do not collide.

using XAct
reset_state!()

# ## 2. Define the manifold and typed indices
# In General Relativity, spacetime is modeled as a manifold.
# `@indices` creates typed index variables bound to that manifold.

M = def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
@indices M a b c d e f

# ## 3. Define a symmetric tensor
# Now define a rank-2 symmetric tensor and fetch a typed handle for expression building.

def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")
T_h = tensor(:T)

# ## 4. Canonicalize a simple symmetry identity
# Because `T` is symmetric, swapping its slots should not change the expression.

ToCanonical(T_h[-b, -a] - T_h[-a, -b])

# > **String API equivalent:** `ToCanonical("T[-b,-a] - T[-a,-b]")`

# ## 5. Add a metric and inspect the induced geometry
# Defining a metric also creates the associated covariant derivative and curvature tensors.

g = def_metric!(-1, "g[-a,-b]", :CD)
Riem = tensor(:RiemannCD)
g_h = tensor(:g)

# ## 6. Verify Riemann tensor symmetries
# The canonicalizer recognizes the standard Riemann identities automatically.

ToCanonical(Riem[-a, -b, -c, -d] + Riem[-a, -c, -d, -b] + Riem[-a, -d, -b, -c])
ToCanonical(Riem[-a, -b, -c, -d] - Riem[-c, -d, -a, -b])

# ## 7. Contract a vector with the metric
# Define a vector and lower its index through metric contraction.

def_tensor!(:V, ["a"], :M)
V_h = tensor(:V)
Contract(V_h[a] * g_h[-a, -b])

# ## 8. Trigger typed validation on purpose
# The typed API catches invalid tensor applications before evaluation.

try
    Riem[-a, -b]
catch e
    println(e)
end

# ## 9. Troubleshoot common fail states
# - **Symbol already exists**: call `reset_state!()` and rerun the tutorial from the top.
# - **Wrong number of slots**: check the tensor rank before indexing.
# - **Manifold mismatch**: ensure every typed index belongs to the same manifold as the tensor slots.

# ## 10. Continue with deeper material
# - For the full typed API: [Typed Expressions (TExpr)](../guide/TExpr.md)
# - For notebook-based practice: [Julia notebook](../notebooks/basics_julia.md)
# - For Python usage: [Python notebook](../notebooks/basics_python.md)
# - For Wolfram workflows: [Wolfram Migration Guide](../wolfram-migration.md)
