# Architecture

`xAct.jl` is the native Julia core of the xAct migration ecosystem. It is designed to be a high-performance, standalone library for symbolic tensor algebra, while also providing hooks for verification and interop.

## Ecosystem Context

The migration project is organized into three pillars:

- **xAct.jl** (This Repo): The native computational engines (`XCore.jl`, `XPerm.jl`, `XTensor.jl`).
- [Elegua](https://github.com/sashakile/elegua) (External): The orchestration layer for parity verification and CI.
- [Chacana](https://github.com/sashakile/chacana) (External): The unified Tensor DSL that connects different engines.

## Computational Layers

The project structure supports both native Julia usage and a robust verification pipeline:

### 1. The Julia Core (xAct.jl)

Located in `src/julia`, this is the primary library. It follows the original xAct design:
- `XCore`: Symbol registry and validation.
- `XPerm`: Group theory and Butler-Portugal canonicalization.
- `XTensor`: Manifolds, tensors, metrics, and curvature operators.

### 2. The Verification Oracle (Wolfram)

A Dockerized Wolfram Engine running the original xAct code. It acts as the "Ground Truth" for proving implementation correctness.

### 3. The sxact-py Wrapper

A thin Python layer (using `juliacall`) that provides an idiomatic interface for Python researchers and integrates with the verification suite.

### 4. Normalization & Comparison

Specialized modules in Python that canonicalize results and perform multi-tier equivalence checks:
- **Normalize**: Lexicographic term sorting and dummy index canonicalization.
- **Compare**: Symbolic (Difference=0) and Numeric (Random Sampling) verification modes.
