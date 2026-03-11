# Architecture

`xAct.jl` is the native Julia core of the xAct migration ecosystem. It is designed to be a high-performance, standalone library for symbolic tensor algebra, while also providing hooks for verification and interop.

## Ecosystem Context

The migration project is organized into three pillars:

- **xAct.jl** (This Repo): The native computational engines (`XCore.jl`, `XPerm.jl`, `XTensor.jl`).
- [Elegua](https://github.com/sashakile/elegua) (External): The orchestration layer for parity verification and CI.
- [Chacana](https://github.com/sashakile/chacana) (External): The unified Tensor DSL that connects different engines.

## Computational Layers

The project structure supports both native Julia usage and a robust verification pipeline:

### Computational Layers (Julia Core)

The native library follows the original xAct design, split into four interoperable modules:

- **XCore.jl**: The foundational symbol registry, expression validator, and session state manager.
- **XPerm.jl**: The group theory engine, implementing the Butler-Portugal algorithm for tensor index canonicalization.
- **XTensor.jl**: The tensor algebra layer, providing manifolds, bundles, metrics, and curvature operators.
- **xCoba.jl**: (Experimental) Support for coordinate bases and component calculations.

### Verification Layer (Wolfram Oracle)

To ensure mathematical correctness, `xAct.jl` is continuously verified against the original Wolfram implementation:
- **The Oracle**: A Dockerized Wolfram Engine running xAct v1.2.0+.
- **Parity Engine**: A specialized test runner that compares Julia and Wolfram results using symbolic and numeric modes.

### Python Interoperability (sxact-py)

A thin Python wrapper (using `PythonCall.jl`) provides an idiomatic interface for researchers in the scientific Python ecosystem and powers the verification suite.
