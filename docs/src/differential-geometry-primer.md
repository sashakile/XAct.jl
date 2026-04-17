# Differential Geometry Primer

This document covers the mathematics underlying `XAct.jl`. It's aimed at
contributors with a programming background who want a working understanding of the
relevant concepts — enough to read tensor algebra code and xAct's notation.

---

## 1. Manifolds

A **manifold** is a space that locally looks like ordinary Euclidean space, but may
have global structure that's more complex. Think of the surface of the Earth: any
small patch looks flat (like ℝ²), but the whole thing is a sphere.

More precisely, an *n-dimensional manifold* M is a topological space where every
point has a neighborhood that is homeomorphic to ℝⁿ.

### Charts, atlases, and coordinate systems

A **chart** (or coordinate patch) is a pair (U, φ) where:

- U ⊆ M is an open subset
- φ: U → ℝⁿ is a homeomorphism (a smooth invertible map to Euclidean space)

The map φ assigns *coordinates* (x¹, x², …, xⁿ) to each point in U.

An **atlas** is a collection of charts that covers all of M. Where two charts
overlap, the transition maps φ₂ ∘ φ₁⁻¹ must be smooth.

**Why this matters for xAct:** xAct's `DefManifold` creates a manifold object and
`DefChart` introduces coordinates. Coordinate expressions live in specific charts;
chart-free (abstract) expressions don't.

---

## 2. Vectors and Tensors

### Tangent spaces

At each point p ∈ M there is a **tangent space** TₚM — the vector space of all
"directions you can move from p." It has dimension n.

Concretely, a tangent vector at p is an equivalence class of curves through p, or
equivalently, a **directional derivative operator**:

```
v = vⁱ ∂/∂xⁱ
```

where ∂/∂xⁱ are the coordinate basis vectors and vⁱ are the components.

### Cotangent spaces

The **cotangent space** Tₚ*M is the dual of TₚM: the space of linear maps
TₚM → ℝ. Elements are called **covectors** or **one-forms**.

The coordinate basis for covectors is dxⁱ, defined by dxⁱ(∂/∂xʲ) = δⁱⱼ.
A covector writes as ω = ωᵢ dxⁱ.

### Tensors as multilinear maps

A **tensor of type (r, s)** at a point is a multilinear map:

```
T: Tₚ*M × … × Tₚ*M × TₚM × … × TₚM → ℝ
       r covector slots          s vector slots
```

In components: T^{a₁…aᵣ}_{b₁…bₛ}

- Upper indices (contravariant) = vector slots
- Lower indices (covariant) = covector slots

A scalar is (0,0), a vector is (1,0), a covector is (0,1), the metric is (0,2).

---

## 3. Tensor Algebra

### Tensor product

Given tensors T of type (r,s) and S of type (p,q), their **tensor product** T⊗S
is a tensor of type (r+p, s+q):

```
(T⊗S)^{ab}_{cd} = T^a_c · S^b_d
```

In xAct: tensors written next to each other are multiplied.

### Contraction

**Contraction** sums over a matching upper and lower index pair, reducing type
(r,s) to (r-1, s-1):

```
Tᵃ_ₐ = Σₐ Tᵃ_ₐ    (trace)
```

In abstract index notation (see below), repeated indices with one up and one down
signal a contraction: `T[a, -a]` in xAct.

### Abstract index notation

xAct uses **abstract index notation** (Penrose notation):

- Indices are *labels*, not component numbers. `v[a]` means the vector v, with
  label `a` marking its single slot.
- A repeated index, one up and one down, means contraction: `T[a, -a]` = trace.
- Concrete components are written with coordinate indices (integers or chart labels).

This notation lets you write tensorial equations that hold in any coordinate system,
without choosing coordinates.

---

## 4. Metric Tensor

The **metric tensor** g is a (0,2) tensor that provides an inner product on each
tangent space:

```
g: TₚM × TₚM → ℝ
g(v, w) = gₐb vᵃ wᵇ
```

In GR the metric has signature (-,+,+,+) (one time, three space dimensions).

### Raising and lowering indices

The metric and its inverse g^{ab} (defined by g^{ac} g_{cb} = δᵃb) convert between
upper and lower indices:

```
vₐ = gₐb vᵇ      (lower)
vᵃ = gᵃᵇ vᵦ      (raise)
```

In xAct: `g[-a, -b]` is the metric; `delta[-a, b]` is the identity tensor.

### Lengths, angles, volumes

- **Length** of a vector: |v|² = g_{ab} vᵃ vᵇ
- **Angle** between vectors: cos θ = g(v,w)/(|v||w|)
- **Volume element**: √|det g| dx¹∧…∧dxⁿ

---

## 5. Differential Forms

**Differential forms** are totally antisymmetric covariant tensors.

- A **0-form** is a function f.
- A **1-form** is a covector ω = ωₐ dxᵃ.
- A **2-form** is F = F_{ab} dxᵃ∧dxᵇ with F_{ab} = -F_{ba}.
- A **p-form** is a rank-(0,p) antisymmetric tensor.

### Wedge product

The **wedge product** of a p-form α and q-form β is a (p+q)-form:

```
(α∧β)_{a₁…aₚb₁…bq} = (p+q)!/(p!q!) α_{[a₁…aₚ} β_{b₁…bq]}
```

where [·] denotes antisymmetrization. The wedge product is graded-commutative:
α∧β = (-1)^{pq} β∧α.

### Exterior derivative

The **exterior derivative** d maps p-forms to (p+1)-forms:

```
(dω)_{a₀a₁…aₚ} = (p+1) ∂_{[a₀} ω_{a₁…aₚ]}
```

Key properties:
- d(df) = 0 for any function f (= d² = 0)
- Leibniz rule: d(α∧β) = dα∧β + (-1)ᵖ α∧dβ

---

## 6. Covariant Derivative

An ordinary partial derivative ∂_a of a tensor does not transform as a tensor.
The **covariant derivative** ∇_a fixes this by accounting for how basis vectors
change across the manifold.

### Connection and parallel transport

A **connection** (or covariant derivative) ∇ specifies how to "transport" vectors
along curves while keeping them "parallel." This requires additional structure beyond
the manifold itself — it's not determined by the topology alone.

The Levi-Civita connection is the unique connection that is:
1. Compatible with the metric: ∇_a g_{bc} = 0
2. Torsion-free: ∇_a ∇_b f = ∇_b ∇_a f for scalars

### Covariant derivative of a tensor

For a vector field v:

```
∇_a v^b = ∂_a v^b + Γ^b_{ac} v^c
```

For a covector ω:

```
∇_a ω_b = ∂_a ω_b - Γ^c_{ab} ω_c
```

The sign flips and the free index goes in the Γ position for each lower index.

### Christoffel symbols

The **Christoffel symbols** Γ^c_{ab} encode the connection in coordinates:

```
Γ^c_{ab} = ½ g^{cd} (∂_a g_{bd} + ∂_b g_{ad} - ∂_d g_{ab})
```

They're symmetric in the lower indices: Γ^c_{ab} = Γ^c_{ba}.

In xAct: `CD[-a]` is ∇_a using the `CD` connection. `ChristoffelCD[a, -b, -c]` gives
the Christoffel symbols.

---

## 7. Curvature

The **Riemann curvature tensor** measures how much parallel transport around a
closed loop rotates vectors:

```
R^d_{cab} v^c = (∇_a ∇_b - ∇_b ∇_a) v^d
```

In components:

```
R^d_{cab} = ∂_a Γ^d_{bc} - ∂_b Γ^d_{ac} + Γ^d_{ae}Γ^e_{bc} - Γ^d_{be}Γ^e_{ac}
```

### Ricci tensor

The **Ricci tensor** is the trace of the Riemann tensor:

```
R_{ab} = R^c_{acb}
```

It's symmetric: R_{ab} = R_{ba}.

### Ricci scalar

The **Ricci scalar** (scalar curvature) is the trace of the Ricci tensor:

```
R = g^{ab} R_{ab} = Rᵃ_a
```

### Einstein tensor

The **Einstein tensor** appears in the Einstein field equations of GR:

```
G_{ab} = R_{ab} - ½ g_{ab} R
```

It's divergence-free: ∇^a G_{ab} = 0 (contracted Bianchi identity).

In xAct: `RiemannCD[-a,-b,-c,-d]`, `RicciCD[-a,-b]`, `RicciScalarCD[]`,
`EinsteinCD[-a,-b]`.

---

## 8. Symmetries of Tensors

### Symmetric and antisymmetric parts

For a rank-(0,2) tensor T:

```
T_{(ab)} = ½(T_{ab} + T_{ba})    symmetric part
T_{[ab]} = ½(T_{ab} - T_{ba})    antisymmetric part
```

In xAct: `(...)` denotes symmetrization, `[...]` antisymmetrization in index lists.

### Symmetries of the Riemann tensor

The Riemann tensor R_{abcd} (fully covariant) has these symmetries:

| Symmetry | Equation |
|---------|---------|
| Antisymmetric in first pair | R_{abcd} = -R_{bacd} |
| Antisymmetric in second pair | R_{abcd} = -R_{abdc} |
| Symmetric under pair swap | R_{abcd} = R_{cdab} |
| First Bianchi identity | R_{a[bcd]} = 0 |
| Second Bianchi identity | ∇_{[e}R_{ab]cd} = 0 |

These symmetries reduce the number of independent components of R from n⁴ to
n²(n²-1)/12 (in 4D: 20 components out of 256).

### Bianchi identities

The **second (differential) Bianchi identity** ∇_{[e}R_{ab]cd} = 0 implies the
contracted form ∇^a G_{ab} = 0, which is the conservation law for the
Einstein tensor.

xAct can verify and apply these symmetries automatically via the
canonicalization routines in `XPerm.jl` (Butler-Portugal algorithm).

---

## Further Reading

- **Misner, Thorne & Wheeler** — *Gravitation* (1973): comprehensive GR reference
- **Wald** — *General Relativity* (1984): rigorous mathematical treatment
- **Nakahara** — *Geometry, Topology and Physics*: differential geometry for physicists
- **xAct manual** at [xact.es](http://xact.es/): xAct-specific notation and usage
