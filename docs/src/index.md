# xAct.jl

!!! info "Project Profile for AI Agents (LLM TL;DR)"
    - **Name**: xAct.jl (Repository: `sxAct`)
    - **Primary Language**: Julia (Computational Core)
    - **Python Distribution**: `xact-py` (Core: `xact`, Testing: `sxact`)
    - **Function**: Symbolic tensor algebra and curvature calculus for General Relativity.
    - **Ecosystem**: Julia port of the Wolfram `xAct` suite.
    - **Verification**: 100% parity verified against Wolfram Engine via `sxact` framework.
    - **License**: GNU General Public License v3.0 (GPL-3.0)

Julia and Python implementations of xAct — a powerful tensor algebra library for general relativity.

## Fast Track (Julia)

Get started in 60 seconds. Open your Julia REPL and run:

```julia
using xAct
M = def_manifold!(:M, 4, [:a, :b])
T = def_tensor!(:T, ["-a", "-b"], :M, symmetry_str="Symmetric[{-a,-b}]")
ToCanonical("T[-b,-a] - T[-a,-b]") # returns "0"
```

## Project Overview

The `xAct.jl` project (hosted in the `sxAct` repository) provides the native, high-performance Julia implementation of the xAct tensor calculus suite. It is designed to be the modern, open-source successor to the Wolfram Language "Gold Standard."

### Implementation & Verification
- **xAct.jl** (Core): The high-performance computational engine written in native Julia.
- **xact-py** (Wrapper): An idiomatic Python interface (`import xact`) to the Julia core.
- **sxact** (Verification): A robust Python framework for automated parity testing against the Wolfram Engine.

### Three Pillars of the Migration
To maintain focus and scalability, the migration effort is divided into three distinct, interoperable projects:

1.  **xAct.jl** (This Repo): The native Julia core and Python wrapper implementations.
2.  **[Elegua](https://github.com/sashakile/elegua)** (External): The orchestration layer used to verify implementation parity against the **Wolfram Oracle**.
3.  **[Chacana](https://github.com/sashakile/chacana)** (External): The language-agnostic tensor DSL and specification.

## Migration Rosetta Stone

| Operation | Wolfram (xAct) | Julia (xAct.jl) | Status |
| :--- | :--- | :--- | :--- |
| **DefManifold** | `DefManifold[M, 4, {a,b}]` | `def_manifold!(:M, 4, [:a, :b])` | ✅ Verified |
| **DefTensor** | `DefTensor[T[-a,-b], M]` | `def_tensor!(:T, ["-a", "-b"], :M)` | ✅ Verified |
| **DefMetric** | `DefMetric[-1, g[-a,-b], CD]` | `def_metric!(-1, "g[-a,-b]", :CD)` | ✅ Verified |
| **ToCanonical** | `ToCanonical[expr]` | `ToCanonical(expr)` | ✅ Verified |
| **Contract** | `ContractMetric[expr]` | `Contract(expr)` | 🏗️ Beta |
| **VarD** | `VarD[g[-a,-b]][expr]` | `VarD("-g[-a,-b]")(expr)` | 🗓️ Planned |
| **IBP** | `IBP[expr, CD]` | `IBP(expr, :CD)` | 🗓️ Planned |

## Installation
See the [Installation Guide](installation.md) for details on setting up the Julia package. **Note**: Docker and the Wolfram Oracle are only required if you intend to run the verification suite.

## Architecture
The implementation follows a layered approach, described in the [Architecture](architecture.md) section.
