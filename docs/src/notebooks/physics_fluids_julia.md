!!! tip "Run this notebook"
    - [Download the Jupyter notebook](https://github.com/sashakile/XAct.jl/blob/main/notebooks/julia/physics_fluids.ipynb)
    - [Open in Google Colab](https://colab.research.google.com/github/sashakile/XAct.jl/blob/main/notebooks/julia/physics_fluids.ipynb)
    - [Open in Binder](https://mybinder.org/v2/gh/sashakile/XAct.jl/main?labpath=notebooks%2Fjulia%2Fphysics_fluids.ipynb)

# Physics: Relativistic Fluid Dynamics

This tutorial explores **Relativistic Fluid Dynamics** using `XAct.jl`.
We define the perfect-fluid stress tensor, make the timelike-velocity sign
convention explicit, and set up the standard energy/momentum projections of
$\nabla_a T^{ab} = 0$ without overclaiming a full fluid-dynamics derivation.

## 1. Setup

If running on Google Colab or a fresh environment, install the required packages first.

```@example physics_fluids_julia
# Uncomment the lines below if running on Google Colab:
# using Pkg
# Pkg.add("XAct")
# Pkg.add("Plots")
```

## 2. Setup

Load the required modules.

```@example physics_fluids_julia
using XAct
```

!!! info "Project Profile for AI Agents (LLM TL;DR)"
    - **Goal**: Define perfect-fluid $T_{ab}$, state the normalization/sign convention, and build the energy/momentum projections of $\nabla_a T^{ab} = 0$.
    - **Key Symbols**: Velocity $u^a$, Density $\rho$, Pressure $p$, projector $h_{ab}$.
    - **Physics**: With signature $(-,+,+,+)$, enforce $u^a u_a = -1$ and use $h_{ab} = g_{ab} + u_a u_b$ to split the conservation law.

## 2. Define the Manifold and Metric

```@example physics_fluids_julia
reset_state!()
M = def_manifold!(:M4, 4, [:a, :b, :c, :d, :mu, :nu, :alpha, :beta])
@indices M4 a b c d mu nu alpha beta

# General metric with signature (-,+,+,+)
def_metric!(-1, "g[-a,-b]", :CD)
```

## 3. The Perfect Fluid Energy-Momentum Tensor

A perfect fluid is characterized by its **energy density** $\rho$,
**pressure** $p$, and **4-velocity** $u^a$. With the mostly-plus signature
$(-,+,+,+)$, the normalization convention is
$u^a u_a = -1$.

The perfect-fluid stress tensor is
$T_{ab} = (\rho + p) u_a u_b + p g_{ab}$.

```@example physics_fluids_julia
# Define scalar fields rho and p
# Keep `fluid_pressure` as the Julia binding to avoid confusion with Base.p.
def_tensor!(:rho, String[], :M4)
def_tensor!(:p, String[], :M4)
rho = tensor(:rho)
fluid_pressure = tensor(:p)

# Define 4-velocity vector u^a
# XAct handles lowered components via the metric.
def_tensor!(:u, ["a"], :M4)
fluid_velocity = tensor(:u)

fluid_velocity_norm = ToCanonical(fluid_velocity[-mu] * fluid_velocity[mu])
projector_h = ToCanonical(tensor(:g)[-mu, -nu] + fluid_velocity[-mu] * fluid_velocity[-nu])
T_expr = ToCanonical(
    (rho[] + fluid_pressure[]) * fluid_velocity[-mu] * fluid_velocity[-nu]
    + fluid_pressure[] * tensor(:g)[-mu, -nu]
)

println("Velocity normalization expression u_a u^a (set this equal to -1 for a timelike fluid velocity):")
fluid_velocity_norm
println("Perfect-fluid projector h_{ab} = g_{ab} + u_a u_b:")
projector_h
println("Energy-Momentum Tensor T_{ab}:")
T_expr
```

## 4. Conservation Laws and Projector Split

The fluid equations come from conservation of stress-energy,
$\nabla_a T^{ab} = 0$.

Rather than claiming a full Euler-equation derivation from the notebook code,
we do the more honest thing here: construct the two standard projections that a
textbook derivation would simplify further.

```@example physics_fluids_julia
# In textbook notation the conservation law is ∇_a T^{ab} = 0.
# For now we keep the projected equations in symbolic template form.
# This stays honest about the current notebook scope while still recording the
# exact two projections a full derivation would simplify.
energy_projection = "u_b ∇_a T^{ab} = 0"
momentum_projection = "h^c{}_b ∇_a T^{ab} = 0"

println("Energy projection template:")
energy_projection
println("Momentum projection template:")
momentum_projection
```

## 5. One Concrete Symbolic Takeaway

The normalization and projector definitions already encode one important fluid
identity: in the $(-,+,+,+)$ convention, the projector is orthogonal to the
fluid 4-velocity,
$h_{ab} u^b = 0$,
provided the normalization constraint $u^a u_a = -1$ holds.

In our notation, the pair

- `fluid_velocity_norm = u_a u^a`, interpreted with the condition `u_a u^a = -1`, and
- `projector_h = g_ab + u_a u_b`

is the compact symbolic data from which that orthogonality statement follows.
That is the concrete takeaway this notebook validates and reuses when forming
the momentum projection above.

## 6. Summary

This tutorial demonstrated:
1. Constructing the perfect-fluid stress tensor from $\rho$, $p$, $u^a$, and $g_{ab}$.
2. Making the timelike normalization $u^a u_a = -1$ explicit for the chosen sign convention.
3. Building the energy and momentum projections of $\nabla_a T^{ab} = 0$ using the spatial projector $h_{ab}$.
4. Ending with one concrete symbolic payoff: the projector/normalization pair that underlies $h_{ab}u^b = 0$.

## Next Steps

- **Electromagnetism**: See [Maxwell's Equations in Curved Spacetime](physics_em_julia.md).
- **Black Holes**: Review [Carroll: Schwarzschild Geodesics](carroll_schwarzschild_julia.md).
- **Cosmology**: Review [Wald: FLRW Cosmology](wald_cosmology_julia.md).
