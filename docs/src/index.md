# XAct.jl

!!! info "Project Profile for AI Agents (LLM TL;DR)"
    - **Name**: XAct.jl (Repository: `sxAct`)
    - **Primary Language**: Julia (Computational Core)
    - **Function**: Symbolic tensor algebra and curvature calculus for General Relativity.
    - **Ecosystem**: Native Julia port of the Wolfram [xAct](http://xact.es/) suite by José M. Martín-García et al.
    - **Verification**: Parity verified against Wolfram Engine via `sxact` test framework.
    - **License**: GNU General Public License v3.0 (GPL-3.0)

A native Julia port of the [xAct](http://xact.es/) tensor algebra suite for general relativity, originally developed for Wolfram Mathematica. Rewrites xPerm, xTensor, xCoba, and Invar in pure Julia for performance, composability, and open access without a Mathematica license.

## Start Here

Follow this newcomer path:

1. [Installation](installation.md) — set up Julia, Python, or the verification stack
2. [Getting Started](getting-started.md) — run the first working Julia or Python examples
3. [Typed Expressions (TExpr)](guide/TExpr.md) — learn the recommended expression API
4. [Basics tutorial](examples/basics.md) or [notebooks](notebooks/basics_julia.md) — continue with guided examples

## What is what?

| Name | Kind | Meaning |
| :--- | :--- | :--- |
| `sxAct` | Repository | The Git repository you clone and browse |
| `XAct.jl` / `XAct` | Julia package and module | The native Julia tensor algebra engine |
| `xact-py` | Python package | The distribution published to PyPI |
| `xact` | Python import | The Python API imported in user code |
| `sxact` | Verification framework | The Python tooling for oracle-based parity tests |

## Fast Track (Julia)

Get started in 60 seconds. Open your Julia REPL and run:

```julia
using XAct

reset_state!()
def_manifold!(:M, 4, [:a, :b, :c, :d])
def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")

@indices M a b c d     # typed index variables
T_h = tensor(:T)       # tensor handle

ToCanonical(T_h[-b,-a] - T_h[-a,-b])  # returns "0"
```

The `@indices` / `tensor()` syntax is the **typed API** — it validates slot counts
and manifold membership at construction time. See [Typed Expressions (TExpr)](guide/TExpr.md)
for the full guide. The string API (`ToCanonical("T[-b,-a] - T[-a,-b]")`) also works
everywhere and can be mixed freely.

## Project Overview

The `XAct.jl` project (hosted in the `sxAct` repository) provides the native Julia implementation of the [xAct](http://xact.es/) tensor calculus suite originally created by José M. Martín-García and collaborators for Wolfram Mathematica. It is designed as the modern, open-source successor — a complete rewrite rather than a wrapper.

### Components
- **XAct.jl** (Core): The computational engine written in native Julia — covers canonicalization (Butler-Portugal/xPerm), contraction, covariant derivatives, perturbation theory, coordinate components (xCoba), Riemann invariants (Invar), and more.
- **sxact** (Verification): A Python framework for automated parity testing against the Wolfram Engine using TOML-defined test cases and oracle snapshots.

## Migration Rosetta Stone

For the full Wolfram-to-Julia mapping table, see [Getting Started](getting-started.md#4-reference-migration-rosetta-stone). For translation tooling and migration workflow, see [Wolfram Migration Guide](wolfram-migration.md).

## Coming from Wolfram xAct?
Use the [Wolfram Migration Guide](wolfram-migration.md) to automatically translate your existing Wolfram code to Julia with the `xact-test translate` CLI.

## Installation
See the [Installation Guide](installation.md) for environment setup details. After installation, continue to [Getting Started](getting-started.md).

## Architecture
The implementation follows a layered approach, described in the [Architecture](architecture.md) section.

## AI Attribution

The majority of this codebase was developed with AI assistance using [Claude Code](https://claude.ai/claude-code), [Gemini](https://gemini.google.com/), and [Amp Code](https://ampcode.com/). All code is human-reviewed and tested against the Wolfram Engine oracle for mathematical correctness. We believe AI-assisted development, when paired with rigorous verification, produces higher-quality scientific software.
