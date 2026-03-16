# Migrating from Wolfram xAct

This guide is for researchers who already use the Wolfram Language `xAct` suite and want to migrate their workflows to `xAct.jl`. It covers the **Wolfram Expression Translator** — a CLI tool that automatically converts your existing Wolfram code into Julia, TOML, or Python.

!!! tip "Already familiar with the Julia API?"
    If you just need a quick reference, see the [Rosetta Stone](getting-started.md#2-reference-migration-rosetta-stone) table.

---

## 1. The Translator: Your Migration Assistant

The `xact-test translate` command parses standard Wolfram xAct expressions and emits equivalent sxAct code. No Wolfram license required — the parser runs entirely locally.

### Quick Example

```bash
# Translate a single expression
xact-test translate -e 'DefManifold[M, 4, {a, b, c, d}]' --to julia
# => xAct.def_manifold!(:M, 4, [:a, :b, :c, :d])
```

### Supported Output Formats

| Format | Flag | Use Case |
|:-------|:-----|:---------|
| JSON | `--to json` | Machine-readable action dicts (default) |
| Julia | `--to julia` | Drop into a Julia REPL or script |
| TOML | `--to toml` | sxAct verification test files |
| Python | `--to python` | Python adapter scripts |

### Translating Multiple Expressions

Separate expressions with semicolons:

```bash
xact-test translate -e \
  'DefManifold[M, 4, {a,b,c,d}]; DefMetric[-1, g[-a,-b], CD]; ToCanonical[g[-b,-a]]' \
  --to julia
```

Output:

```julia
xAct.def_manifold!(:M, 4, [:a, :b, :c, :d])
xAct.def_metric!(-1, "g[-a, -b]", :CD)
xAct.ToCanonical("g[-b, -a]")
```

### Translating a `.wl` File

If you have an existing Wolfram script:

```bash
xact-test translate --file my_notebook.wl --to julia > my_notebook.jl
```

---

## 2. Interactive REPL

For an interactive migration session, use the REPL:

```bash
# Full mode: parse, translate, and execute in Julia
xact-test repl

# Translate-only mode: no Julia runtime needed
xact-test repl --no-eval
```

In the REPL, type Wolfram expressions and see the Julia translation (and result, in full mode):

```
xact> DefManifold[M, 4, {a, b, c, d}]
  julia: xAct.def_manifold!(:M, 4, [:a, :b, :c, :d])

xact> DefMetric[-1, g[-a,-b], CD]
  julia: xAct.def_metric!(-1, "g[-a, -b]", :CD)

xact> ToCanonical[g[-b,-a] - g[-a,-b]]
  julia: xAct.ToCanonical("g[-b, -a] - g[-a, -b]")
  result: 0
```

### Session Export

After building up a session, export the accumulated commands:

```
xact> :to julia
xact> :to toml
xact> :to python
```

This is useful for converting an interactive exploration into a reproducible script or test file.

---

## 3. Supported Actions

The translator recognizes these Wolfram xAct functions:

| Wolfram Function | Translated Action | Notes |
|:-----------------|:------------------|:------|
| `DefManifold[M, 4, {a,b}]` | `def_manifold!` | |
| `DefMetric[-1, g[-a,-b], CD]` | `def_metric!` | Auto-creates Riemann, Ricci, Weyl, Christoffel |
| `DefTensor[T[-a,-b], M]` | `def_tensor!` | Symmetries carried through |
| `DefTensor[T[-a,-b], M, Symmetric[{-a,-b}]]` | `def_tensor!` | `symmetry_str` kwarg |
| `ToCanonical[expr]` | `ToCanonical` | Butler-Portugal canonicalization |
| `ContractMetric[expr]` | `Contract` | Metric contraction |
| `Simplification[expr]` | `Simplify` | Iterative Contract + ToCanonical |
| `SortCovDs[expr]` | `CommuteCovDs` / `SortCovDs` | Covariant derivative ordering |
| `Perturbation[expr]` | `Perturb` | Perturbation expansion |
| `VarD[field][CD]expr` | `VarD` | Euler-Lagrange variation |
| `IBP[expr, v]` | `IBP` | Integration by parts |

Unrecognized functions are passed through as `eval(...)` with a warning.

---

## 4. Complete Migration Walkthrough

Here is a typical Wolfram xAct session and its Julia equivalent.

### Wolfram (original)

```wolfram
DefManifold[M, 4, {a, b, c, d, e, f}]
DefMetric[-1, g[-a, -b], CD]
DefTensor[T[-a, -b], M, Symmetric[{-a, -b}]]

(* Canonicalize a symmetric tensor *)
ToCanonical[T[-b, -a] - T[-a, -b]]
(* => 0 *)

(* Contract with the metric *)
ContractMetric[g[a, b] T[-a, -b]]
(* => T[a, a] — the trace *)

(* Simplify a Riemann expression *)
Simplification[RiemannCD[-a, -b, -c, -d] g[a, c]]
```

### Julia (translated)

Translate the above in one shot:

```bash
xact-test translate -e \
  'DefManifold[M, 4, {a,b,c,d,e,f}]; DefMetric[-1, g[-a,-b], CD]; DefTensor[T[-a,-b], M, Symmetric[{-a,-b}]]; ToCanonical[T[-b,-a] - T[-a,-b]]; ContractMetric[g[a,b] T[-a,-b]]' \
  --to julia
```

Or write the equivalent Julia directly:

```julia
using xAct
reset_state!()

M = def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
g = def_metric!(-1, "g[-a,-b]", :CD)
T = def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")

ToCanonical("T[-b, -a] - T[-a, -b]")   # => "0"
Contract("g[a, b] T[-a, -b]")           # => trace
Simplify("RiemannCD[-a, -b, -c, -d] g[a, c]")
```

### As a TOML Test

```bash
xact-test translate -e \
  'DefManifold[M, 4, {a,b,c,d}]; DefMetric[-1, g[-a,-b], CD]; ToCanonical[g[-b,-a]]' \
  --to toml
```

Produces a ready-to-run sxAct verification test file.

---

## 5. Key Differences from Wolfram xAct

| Concept | Wolfram | Julia |
|:--------|:--------|:------|
| **Names** | Bare symbols: `M`, `T` | Julia Symbols: `:M`, `:T` |
| **Indices** | `T[-a, -b]` | String: `"-a"`, `"-b"` (in API calls) |
| **State** | Global kernel | Global registry; `reset_state!()` to clear |
| **Side effects** | Implicit | Explicit `!` suffix: `def_manifold!`, `def_tensor!` |
| **Contraction** | `ContractMetric` | `Contract` |
| **Simplify** | `Simplification` | `Simplify` (iterative Contract + ToCanonical) |
| **CovD ordering** | `SortCovDs` | `CommuteCovDs` (or `SortCovDs`) |
| **Auto-tensors** | `DefMetric` creates Riemann etc. | Same: `def_metric!` auto-creates all curvature tensors |
| **Perturbation** | `Perturbation[expr]` | `perturb(expr, order)` — explicit order argument |
| **License** | Wolfram Mathematica license | Free and open source (GPL-3.0) |

---

## 6. Tips for a Smooth Migration

1. **Start with the REPL.** Use `xact-test repl` to interactively translate your expressions and verify they produce the same results.

2. **Translate file-by-file.** Use `xact-test translate --file notebook.wl --to julia` to convert existing notebooks.

3. **Check the warnings.** If the translator emits "Unrecognized function" warnings, the function may need manual translation. File an issue if you think it should be supported.

4. **Use `reset_state!()`** at the top of Julia scripts to ensure a clean session — just like restarting the Wolfram kernel.

5. **Run the verification suite** to confirm parity with Wolfram results:

    ```bash
    uv run xact-test run tests/xtensor/canonicalization.toml \
      --adapter julia --oracle-mode snapshot --oracle-dir oracle
    ```

---

## Next Steps

- [Getting Started](getting-started.md) — Full Julia tutorial from scratch
- [Basics Tutorial](examples/basics.md) — Step-by-step walkthrough with Julia, Python, and Wolfram examples
- [Feature Status](theory/STATUS.md) — What's implemented and verified
- [Architecture](architecture.md) — How xAct.jl is structured
