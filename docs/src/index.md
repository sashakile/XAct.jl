# XAct.jl

!!! info "Project Profile for AI Agents (LLM TL;DR)"
    - **Name**: XAct.jl (Repository: `XAct.jl`)
    - **Primary language**: Julia
    - **Purpose**: Symbolic tensor algebra and curvature calculus for general relativity
    - **Python package**: `xact-py` (import as `xact`)
    - **Verification**: Oracle-based parity tests via `sxact`
    - **License**: GNU General Public License v3.0 (GPL-3.0)

XAct.jl is the native Julia port of the Wolfram [xAct](http://xact.es/) suite. Start here if you want the project overview, the newcomer path, and the map of names used across the repository, Julia package, Python package, and verification tooling.

## Start with the canonical newcomer path

Choose one path and follow it in order:

1. [Installation](installation.md) — set up Julia, Python, or the verification stack
2. [Getting Started](getting-started.md) — run the first working Julia or Python examples
3. [Typed Expressions (TExpr)](guide/TExpr.md) — learn the recommended expression API
4. [Basics tutorial](examples/basics.md) or [notebooks](notebooks/basics_julia.md) — continue with guided practice

## Use the page that matches your goal

| Goal | Go to |
| :--- | :--- |
| Install the project | [Installation](installation.md) |
| Run the first working examples | [Getting Started](getting-started.md) |
| Learn the typed expression API | [Typed Expressions (TExpr)](guide/TExpr.md) |
| Work through a guided Julia tutorial | [Basics tutorial](examples/basics.md) |
| Migrate existing Wolfram workflows | [Wolfram Migration Guide](wolfram-migration.md) |
| Look up Wolfram-to-Julia mappings | [Wolfram Translation Reference](wolfram-translation-reference.md) |
| Understand the package and module names | [Naming and product map](naming.md) |
| Inspect API details | [Reference](api-julia.md) |

## Understand the project naming

| Name | Kind | Meaning |
| :--- | :--- | :--- |
| `XAct.jl` | Repository | The Git repository you clone and browse |
| `XAct.jl` / `XAct` | Julia package and module | The native Julia tensor algebra engine |
| `xact-py` | Python package | The distribution published to PyPI |
| `xact` | Python import | The Python API imported in user code |
| `sxact` | Verification framework | The Python tooling for oracle-based parity tests |

## Know what the project contains

The project has two user-facing layers:

- **XAct.jl** — the Julia computational engine for canonicalization, contraction, covariant derivatives, perturbation theory, coordinate components, and invariants.
- **xact-py / xact** — the Python wrapper around the Julia core.

It also has one project-facing support layer:

- **sxact** — the verification framework used to compare results against Wolfram Engine snapshots.

## Try the Julia fast track

If you already have Julia installed, this is the shortest successful session:

```julia
using XAct

reset_state!()
def_manifold!(:M, 4, [:a, :b, :c, :d])
def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")

@indices M a b c d
T_h = tensor(:T)

ToCanonical(T_h[-b,-a] - T_h[-a,-b])
```

The typed API validates index usage before evaluation. For the full typed-expression model, continue to [Typed Expressions (TExpr)](guide/TExpr.md).

## Continue based on where you are coming from

- **New to the project:** start with [Installation](installation.md), then [Getting Started](getting-started.md)
- **Already using Wolfram xAct:** use the [Wolfram Migration Guide](wolfram-migration.md)
- **Looking for API facts:** go to the [Julia API](api-julia.md) or [Python API](api-python.md)
- **Evaluating implementation status:** read the [Feature Matrix](status.md)

## Troubleshooting the first page mismatch

| Situation | Best page |
| :--- | :--- |
| “I need commands, not overview.” | [Installation](installation.md) or [Getting Started](getting-started.md) |
| “I need Wolfram mappings, not onboarding.” | [Wolfram Translation Reference](wolfram-translation-reference.md) |
| “I need the typed API details.” | [Typed Expressions (TExpr)](guide/TExpr.md) |
| “I need package naming clarified.” | [Naming and product map](naming.md) |

## Project note

Most of the codebase was developed with AI assistance and then checked by humans and by oracle-backed verification. The mathematical trust story depends on both implementation review and parity testing.
