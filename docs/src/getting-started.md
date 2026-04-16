# Getting Started with XAct.jl

!!! info "LLM TL;DR"
    - Complete [Installation](installation.md) first
    - Install from GitHub: `Pkg.add(url="https://github.com/sashakile/XAct.jl")`
    - Julia entry point: `using XAct`, then `def_manifold!`, `def_metric!`, `@indices`, `tensor()`
    - Typed API is recommended; string API also works
    - Python entry point: `import xact`
    - For Wolfram mappings, use [Wolfram Translation Reference](wolfram-translation-reference.md)

This page shows the first successful Julia and Python workflows. You should already have the project installed before using this guide.

## Confirm the prerequisite state

Before starting, make sure you have completed [Installation](installation.md).
That page is the source of truth for Julia, Python, and verification setup.

!!! note "Julia General Registry"
    `XAct.jl` is not yet registered in the Julia General Registry.
    Install it from the GitHub URL shown in [Installation](installation.md).

## Run the first Julia session

The Julia REPL is the primary entry point. The typed API is recommended because it validates expressions as you build them.

```julia
using XAct

reset_state!()
def_manifold!(:M, 4, [:a, :b, :c, :d])
def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")

@indices M a b c d
T_h = tensor(:T)

ToCanonical(T_h[-b,-a] - T_h[-a,-b])
```

Expected result:

```julia
"0"
```

## Choose between typed and string expressions

Both interfaces are supported.
Use the typed API for new code and interactive work.
Use the string API when pasting short expressions from Wolfram-oriented material.

| | Typed API | String API |
|---|---|---|
| Syntax | `T_h[-b,-a] - T_h[-a,-b]` | `"T[-b,-a] - T[-a,-b]"` |
| Validation timing | At construction | Inside the engine |
| IDE ergonomics | Better | Minimal |
| Best use | New code, notebooks, REPL work | Quick one-liners, pasted expressions |

The typed API still serializes to the string-based engine internally.

## Add a metric and inspect curvature identities

A metric definition creates the associated covariant derivative and curvature tensors.

```julia
reset_state!()
def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
def_metric!(-1, "g[-a,-b]", :CD)

@indices M a b c d e f
Riem = tensor(:RiemannCD)

ToCanonical(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c])
ToCanonical(Riem[-a,-b,-c,-d] - Riem[-c,-d,-a,-b])
```

Both calls should return `"0"`.

## Run the first Python session

The Python package wraps the Julia core with a snake-case API.

```python
import xact

xact.reset()
M = xact.Manifold("M", 4, ["a", "b", "c", "d"])
T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")

a, b, c, d = xact.indices(M)
T_h = xact.tensor("T")

xact.canonicalize(T_h[-b,-a] - T_h[-a,-b])
```

Expected result:

```python
"0"
```

For a full walkthrough, see the [Python notebook](https://github.com/sashakile/XAct.jl/blob/main/notebooks/python/basics.ipynb).

## Continue to the right follow-up document

| If you want to… | Read… |
| :--- | :--- |
| Learn the typed-expression model in detail | [Typed Expressions (TExpr)](guide/TExpr.md) |
| Work through a guided Julia tutorial | [Basics tutorial](examples/basics.md) |
| Use notebooks instead of the REPL | [Julia notebook](notebooks/basics_julia.md) or [Python notebook](notebooks/basics_python.md) |
| Migrate Wolfram code | [Wolfram Migration Guide](wolfram-migration.md) |
| Look up Wolfram-to-Julia mappings | [Wolfram Translation Reference](wolfram-translation-reference.md) |

## Troubleshooting first-run failures

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `Package XAct not found` | Julia package not installed in the active environment | Repeat the Julia install steps in [Installation](installation.md) |
| `UndefVarError` for tensor names | Session state was reset or setup cells were skipped | Re-run the setup block from the top |
| “Symbol already exists” | You redefined a manifold or tensor in the same session | Run `reset_state!()` and define the session again |
| Typed expression errors about slots or manifolds | Invalid index usage | Check the tensor rank and the manifold bound to each index |

## What this page does not cover

This page is intentionally limited to successful first runs.
It does not try to be the Wolfram migration reference, the full typed-expression manual, or the API reference.
Use the linked pages above for those purposes.
