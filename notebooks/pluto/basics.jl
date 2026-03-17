### A Pluto.jl notebook ###
# v0.20.4

using Markdown
using InteractiveUtils

# ╔═╡ a1000001-0000-0000-0000-000000000001
begin
    import Pkg
    Pkg.activate(joinpath(@__DIR__, "..", ".."))
    using xAct
end

# ╔═╡ a1000002-0000-0000-0000-000000000002
md"""
# sxAct.jl — Interactive Tutorial

This Pluto notebook introduces the core workflow of `xAct.jl`:
manifolds, metrics, canonicalization, and curvature.

Each cell is **reactive** — editing a definition automatically re-evaluates
all dependent cells.
"""

# ╔═╡ a1000003-0000-0000-0000-000000000003
md"## 1. Define a Manifold"

# ╔═╡ a1000004-0000-0000-0000-000000000004
begin
    reset_state!()
    M = def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
end

# ╔═╡ a1000005-0000-0000-0000-000000000005
md"""
## 2. Define a Metric

Lorentzian signature ``(-,+,+,+)``. This automatically creates
Riemann, Ricci, RicciScalar, Weyl, Einstein, and Christoffel tensors.
"""

# ╔═╡ a1000006-0000-0000-0000-000000000006
g = def_metric!(-1, "g[-a,-b]", :CD)

# ╔═╡ a1000007-0000-0000-0000-000000000007
md"""
## 3. Canonicalization

The Butler-Portugal algorithm brings tensor expressions to canonical form.
"""

# ╔═╡ a1000008-0000-0000-0000-000000000008
ToCanonical("g[-b,-a] - g[-a,-b]")

# ╔═╡ a1000009-0000-0000-0000-000000000009
begin
    def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")
    ToCanonical("T[-b,-a] - T[-a,-b]")
end

# ╔═╡ a100000a-0000-0000-0000-000000000001
md"""
## 4. Contraction

Lower an index with the metric — ``V_b = V^a g_{ab}``:
"""

# ╔═╡ a100000b-0000-0000-0000-000000000001
begin
    def_tensor!(:V, ["a"], :M)
    Contract("V[a] * g[-a,-b]")
end

# ╔═╡ a100000c-0000-0000-0000-000000000001
md"""
## 5. Riemann Tensor Identities

First Bianchi identity — should vanish:
"""

# ╔═╡ a100000d-0000-0000-0000-000000000001
ToCanonical("RiemannCD[-a,-b,-c,-d] + RiemannCD[-a,-c,-d,-b] + RiemannCD[-a,-d,-b,-c]")

# ╔═╡ a100000e-0000-0000-0000-000000000001
md"""
## 6. Perturbation Theory

Perturb the metric to first order:
"""

# ╔═╡ a100000f-0000-0000-0000-000000000001
begin
    def_tensor!(:h, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")
    def_perturbation!(:h, :g, 1)
    perturb("g[-a,-b]", 1)
end

# ╔═╡ Cell order:
# ╟─a1000002-0000-0000-0000-000000000002
# ╠═a1000001-0000-0000-0000-000000000001
# ╟─a1000003-0000-0000-0000-000000000003
# ╠═a1000004-0000-0000-0000-000000000004
# ╟─a1000005-0000-0000-0000-000000000005
# ╠═a1000006-0000-0000-0000-000000000006
# ╟─a1000007-0000-0000-0000-000000000007
# ╠═a1000008-0000-0000-0000-000000000008
# ╠═a1000009-0000-0000-0000-000000000009
# ╟─a100000a-0000-0000-0000-000000000001
# ╠═a100000b-0000-0000-0000-000000000001
# ╟─a100000c-0000-0000-0000-000000000001
# ╠═a100000d-0000-0000-0000-000000000001
# ╟─a100000e-0000-0000-0000-000000000001
# ╠═a100000f-0000-0000-0000-000000000001
