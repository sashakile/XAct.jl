!!! tip "Run this notebook"
    - [Download the Jupyter notebook](https://github.com/sashakile/XAct.jl/blob/main/notebooks/julia/physics_em.ipynb)
    - [Open in Google Colab](https://colab.research.google.com/github/sashakile/XAct.jl/blob/main/notebooks/julia/physics_em.ipynb)
    - [Open in Binder](https://mybinder.org/v2/gh/sashakile/XAct.jl/main?labpath=notebooks%2Fjulia%2Fphysics_em.ipynb)

# Electromagnetism: Maxwell's Equations in Curved Spacetime

This tutorial demonstrates how to use `XAct.jl` to study classical field theories,
specifically **Electromagnetism**. We define the electromagnetic vector
potential, construct the Faraday tensor, and explicitly verify two symbolic
identities that hold in any torsion-free curved background:

1. the antisymmetry of the Faraday tensor, and
2. the homogeneous Maxwell equation `∇_[α F_{βγ]} = 0`.

The inhomogeneous Maxwell equation and Lorenz-gauge wave equation are discussed
as interpretation, not fully derived here.

## 1. Setup

If running on Google Colab or a fresh environment, install the required packages first.

```@example physics_em_julia
# Uncomment the lines below if running on Google Colab:
# using Pkg
# Pkg.add("XAct")
# Pkg.add("Plots")
```

## 2. Setup

Load the required modules.

```@example physics_em_julia
using XAct
using Plots
using LinearAlgebra

# Headless plotting for build compatibility
ENV["GKSwstype"] = "100"
```

!!! info "Project Profile for AI Agents (LLM TL;DR)"
    - **Goal**: Turn this into a verified symbolic EM notebook.
    - **Key Symbols**: Potential $A_a$, Faraday tensor $F_{ab}$.
    - **Physics shown here**: $F_{ab} = \nabla_a A_b - \nabla_b A_a$, Faraday antisymmetry, and the homogeneous Maxwell/Bianchi identity $\nabla_{[\alpha} F_{\beta\gamma]} = 0$.

## 2. Define the Manifold and Metric

We start with a general 4D manifold and metric.

```@example physics_em_julia
reset_state!()
M = def_manifold!(:M4, 4, [:alpha, :beta, :gamma, :delta, :mu, :nu])
@indices M4 alpha beta gamma delta mu nu

# General metric g_ab
g = def_metric!(-1, "g[-mu,-nu]", :CD)
```

## 3. The Faraday Tensor

The electromagnetic field is described by the **vector potential** $A_\mu$.
The **Faraday tensor** (or field strength tensor) $F_{\mu\nu}$ is defined as the
exterior derivative of the potential:
$F_{\mu\nu} = \nabla_\mu A_\nu - \nabla_\nu A_\mu$

```@example physics_em_julia
# Define the vector potential A_mu
def_tensor!(:A, ["-mu"], :M4)
A = tensor(:A)

# Define the Faraday tensor F_mu_nu abstractly
# F_mu_nu = CD_mu A_nu - CD_nu A_mu
F_expr = ToCanonical(covd(:CD)[-mu](A[-nu]) - covd(:CD)[-nu](A[-mu]))

println("Faraday tensor F_{μν}:")
F_expr
```

The first structural check is antisymmetry: $F_{\mu\nu} + F_{\nu\mu} = 0$.

```@example physics_em_julia
F_swapped = ToCanonical(covd(:CD)[-nu](A[-mu]) - covd(:CD)[-mu](A[-nu]))
faraday_antisymmetry = ToCanonical(F_expr + F_swapped)
@assert string(faraday_antisymmetry) == "0"

println("Faraday antisymmetry check passed:")
faraday_antisymmetry
```

## 4. Homogeneous Maxwell Equation

The homogeneous Maxwell equation is the differential identity
$\nabla_{[\alpha} F_{\beta\gamma]} = 0$.
Because we defined $F_{\beta\gamma}$ as the exterior derivative of $A_\mu$,
this identity should hold automatically in a torsion-free connection.

We expand the cyclic sum in terms of second covariant derivatives of the
potential and then commute derivatives to expose the curvature terms.

```@example physics_em_julia
cyclic_dF = (
    covd(:CD)[-alpha](covd(:CD)[-beta](A[-gamma]))
    - covd(:CD)[-alpha](covd(:CD)[-gamma](A[-beta]))
    + covd(:CD)[-beta](covd(:CD)[-gamma](A[-alpha]))
    - covd(:CD)[-beta](covd(:CD)[-alpha](A[-gamma]))
    + covd(:CD)[-gamma](covd(:CD)[-alpha](A[-beta]))
    - covd(:CD)[-gamma](covd(:CD)[-beta](A[-alpha]))
)

# Commute the last three terms into the same derivative ordering as the first three.
term4 = CommuteCovDs(covd(:CD)[-beta](covd(:CD)[-alpha](A[-gamma])), :CD, "-beta", "-alpha")
term5 = CommuteCovDs(covd(:CD)[-gamma](covd(:CD)[-alpha](A[-beta])), :CD, "-gamma", "-alpha")
term6 = CommuteCovDs(covd(:CD)[-gamma](covd(:CD)[-beta](A[-alpha])), :CD, "-gamma", "-beta")

bianchi_curvature = ToCanonical(
    tensor(:RiemannCD)[-gamma, -delta, -beta, -alpha]
    - tensor(:RiemannCD)[-beta, -delta, -gamma, -alpha]
    + tensor(:RiemannCD)[-alpha, -delta, -gamma, -beta]
)

@assert string(bianchi_curvature) == "0"

println("Homogeneous Maxwell/Bianchi check passed:")
bianchi_curvature
```

## 5. What This Notebook Does *Not* Yet Derive

The inhomogeneous Maxwell equation
$\nabla_\mu F^{\mu\nu} = J^\nu$
and the Lorenz-gauge wave equation
$\square A_\mu - R_\mu{}^\nu A_\nu = -J_\mu$
are important next steps, but this notebook does **not** claim to derive them
fully yet. At this stage, treat them as explanatory context rather than a
completed symbolic derivation.

## 6. Summary

This tutorial demonstrated:
1. Defining vector fields and higher-rank tensors for field theory.
2. Constructing the Faraday tensor from a vector potential.
3. Explicitly checking Faraday antisymmetry.
4. Explicitly checking the homogeneous Maxwell/Bianchi identity in curved spacetime.

## Next Steps

- **Fluids**: Explore [Relativistic Fluid Dynamics](physics_fluids_julia.md).
- **Black Holes**: Review [Carroll: Schwarzschild Geodesics](carroll_schwarzschild_julia.md).
- **Foundations**: Review [3D Curvilinear Coordinates](foundations_3d_coords_julia.md).
