# Key Concepts in xAct.jl

This page explains the fundamental concepts and design decisions in the `xAct.jl` implementation.

## 1. Symbol Registry

`xAct.jl` maintains a global registry of manifolds, vbundles, and tensors. This mimics the stateful nature of the original Wolfram implementation, allowing for a more direct migration path.

- **Stateful Definitions**: Functions that modify the global registry end in `!` by convention (e.g., `def_tensor!`, `def_manifold!`).
- **Persistence**: Symbols defined in one part of your script are available globally until `reset_state!()` is called.
- **Validation**: Name collisions are checked at definition time.

## 2. Indices and Abstract Notation

We follow the standard xAct notation for indices:

- **Contravariant (Up)**: Represented by the symbol itself (e.g., `:a`).
- **Covariant (Down)**: Represented by a string or symbol with a minus sign (e.g., `"-a"` or `:-a`).
- **Abstract Dummy Indices**: Indices are treated as abstract labels. The engine handle renaming and canonicalization automatically using the Butler-Portugal algorithm.

## 3. The Typed Expression Layer (TExpr)

While the core engine operates on strings and symbols for maximum compatibility with Wolfram, we provide a **Typed Expression Layer** for a more modern Julia/Python experience.

- **Immediate Validation**: Checks for correct number of slots and manifold membership at construction time.
- **Operator Overloading**: Use `*`, `+`, and `-` directly on tensor objects.
- **Current Boundary**: The typed layer improves ergonomics and catches mistakes earlier, but still serializes expressions into the existing string-based engine internally.

## 4. Parity Verification

A core pillar of the project is **mathematical correctness**. Every operation is verified against the original Wolfram implementation:

- **Oracle Comparison**: Results are compared with those from a live Wolfram Engine or pre-recorded snapshots.
- **Multiple Tiers**: Verification happens at the string level, symbolic level, and sometimes numeric level.
- **Continuous Testing**: The CI suite runs hundreds of parity tests on every commit.

## 5. Portability (Julia & Python)

`xAct.jl` is designed as a polyglot library:
- **Julia Core**: High-performance implementation in native Julia.
- **Python Wrapper**: Snake-case API using `PythonCall.jl`, allowing seamless use in Jupyter notebooks alongside `NumPy` and `SymPy`.
