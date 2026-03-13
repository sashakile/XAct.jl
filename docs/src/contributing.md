# Contributing

We welcome contributions to `xAct.jl` (the Julia core) and the `sxact` verification framework.

## Getting Started

Please see the root [CONTRIBUTING.md](https://github.com/sashakile/sxAct/blob/main/CONTRIBUTING.md) for detailed instructions on:
- Setting up the Julia development environment.
- Setting up the Python and Docker verification environment.
- Running the test suites.
- Following our code style and quality standards.

## Contribution Areas

### 1. Mathematical Implementation (Julia)
- Adding new xAct-compatible functions (e.g., `LieD`, exterior calculus, spinors).
- Optimizing permutation group algorithms in `XPerm.jl`.
- Implementing the multi-term symmetry engine (Invar).
- Extending xCoba coordinate component support in `XTensor.jl`.

### 2. Verification & Tooling (Python)
- Adding new TOML test cases for existing operations.
- Improving the normalization pipeline (regex and AST-based).
- Expanding the property-based test catalog.
- Improving oracle snapshot tooling.

### 3. Documentation & Tutorials
- Writing new Literate.jl tutorials in `docs/examples/`.
- Improving the differential geometry primer.
- Adding worked examples for general relativity use-cases.

## Testing Your Changes

Before submitting a PR, please ensure:
1. `julia --project=. test/runtests.jl` passes.
2. `uv run pytest` passes.
3. `just docs` builds the documentation without errors.
