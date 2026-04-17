```@meta
EditURL = "../../examples/basics.jl"
```

# Basics Tutorial

This tutorial introduces the core concepts of `xAct.jl` and shows how to perform
basic tensor algebra operations. We provide examples in **Julia**, **Python**,
and the original **Wolfram Language (xAct)** to help with migration.

Expressions are written using the **typed API** — index objects and operator
overloading that validates slot counts and manifold membership at construction
time. The string API (`ToCanonical("T[-a,-b]")`) still works everywhere and is
noted as an equivalent alternative.

## 1. Setup
First, we load the `xAct` module.

**Julia**

````@example basics
using XAct
reset_state!()
````

**Python**
```python
import xact
xact.reset()
```

## 2. Defining a Manifold
In General Relativity, our spacetime is represented as a manifold.
In `xAct.jl`, we use `def_manifold!`. The `!` indicates that this function
modifies the global session state.

`@indices` declares typed index variables bound to the manifold.
`-a` then gives a covariant (down) index.

**Julia**

````@example basics
M = def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
@indices M a b c d e f
````

**Python**
```python
M = xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])
a, b, c, d, e, f = xact.indices(M)
```

**Wolfram (xAct)**
```wolfram
DefManifold[M, 4, {a, b, c, d, e, f}]
```

## 3. Defining Tensors
Now we define a symmetric rank-2 tensor $T_{ab}$.
After definition, `tensor()` returns a handle for typed expression building.

**Julia**

````@example basics
def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")
T_h = tensor(:T)
````

**Python**
```python
T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")
T_h = xact.tensor("T")
```

**Wolfram (xAct)**
```wolfram
DefTensor[T[-a, -b], M, Symmetric[{-a, -b}]]
```

## 4. Canonicalization
One of the most powerful features of xAct is its ability to canonicalize
tensor expressions using the Butler-Portugal algorithm.

Since $T$ is symmetric, $T_{ba} - T_{ab} = 0$.

**Julia**

````@example basics
ToCanonical(T_h[-b, -a] - T_h[-a, -b])
````

> **String API equivalent:** `ToCanonical("T[-b,-a] - T[-a,-b]")`

**Python**
```python
xact.canonicalize(T_h[-b,-a] - T_h[-a,-b])  # or xact.canonicalize("T[-b,-a] - T[-a,-b]")
```

**Wolfram (xAct)**
```wolfram
ToCanonical[T[-b, -a] - T[-a, -b]]
(* returns 0 *)
```

## 5. Defining a Metric
The metric tensor $g_{ab}$ is fundamental to defining geometry and curvature.
In `xAct.jl`, defining a metric automatically creates its associated
covariant derivative (`CD`), Riemann, Ricci, Weyl, Einstein, and Christoffel tensors.

**Julia**

````@example basics
g = def_metric!(-1, "g[-a,-b]", :CD)
Riem = tensor(:RiemannCD)
g_h = tensor(:g)
````

**Python**
```python
g = xact.Metric(M, "g", signature=-1, covd="CD")
Riem = xact.tensor("RiemannCD")
```

**Wolfram (xAct)**
```wolfram
DefMetric[-1, g[-a, -b], CD]
```

## 6. Riemann Tensor Identities
The Riemann tensor satisfies well-known symmetries that the canonicalizer
automatically recognizes.

First Bianchi identity — $R_{abcd} + R_{acdb} + R_{adbc} = 0$:

**Julia**

````@example basics
ToCanonical(Riem[-a, -b, -c, -d] + Riem[-a, -c, -d, -b] + Riem[-a, -d, -b, -c])
````

**Python**
```python
xact.canonicalize(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c])
```

Pair symmetry — $R_{abcd} = R_{cdab}$:

**Julia**

````@example basics
ToCanonical(Riem[-a, -b, -c, -d] - Riem[-c, -d, -a, -b])
````

**Python**
```python
xact.canonicalize(Riem[-a,-b,-c,-d] - Riem[-c,-d,-a,-b])
```

## 7. Contraction
`Contract` lowers/raises indices via the metric. Define a vector $V^a$
and lower its index to get $V_b$:

**Julia**

````@example basics
def_tensor!(:V, ["a"], :M)
V_h = tensor(:V)
Contract(V_h[a] * g_h[-a, -b])
````

**Python**
```python
V = xact.Tensor("V", ["a"], M)
V_h = xact.tensor("V")
xact.contract(V_h[a] * g[-a,-b])
```

## 8. Validation
The typed API catches mistakes at construction time — before the expression
reaches the engine:

**Julia**

````@example basics
try
    Riem[-a, -b]     ## ERROR: RiemannCD has 4 slots, got 2
catch e
    println(e)
end
````

**Python**
```python
try:
    Riem[-a,-b]   # IndexError: RiemannCD has 4 slots, got 2
except IndexError as err:
    print(err)
```

## 9. Common Pitfalls
- **Name Collisions**: Defining a manifold or tensor with an existing name throws an error.
- **Global State**: The `!` functions modify the global session. Re-running a cell
  in a notebook may trigger a "Symbol already exists" error — call `reset_state!()` first.

## 10. Next Steps
Now that you've mastered the basics, check out:
- [Differential Geometry Primer](../differential-geometry-primer.md)
- [Feature Status](../status.md)

---

*This page was generated using [Literate.jl](https://github.com/fredrikekre/Literate.jl).*
