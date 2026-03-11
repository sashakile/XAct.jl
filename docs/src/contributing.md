# Contributing

We welcome contributions to `xAct.jl` (the Julia core) and the `sxact-py` verification framework.

## Getting Started

Please see the root [CONTRIBUTING.md](https://github.com/sashakile/sxAct/blob/main/CONTRIBUTING.md) for detailed instructions on:
- Setting up the Julia development environment.
- Setting up the Python and Docker verification environment.
- Running the multi-tier test suite.
- Following our code style and quality standards.

## Contribution Areas

### 1. Mathematical Implementation (Julia)
- Adding new xAct-compatible functions (e.g., `LieD`, `Inertial`, etc.).
- Optimizing permutation group algorithms in `XPerm.jl`.
- Implementing advanced tensor identities in `XTensor.jl`.

### 2. Verification & Tooling (Python)
- Adding new normalization rules to the pipeline.
- Improving the oracle performance and reliability.
- Expanding the property-based test catalog.

### 3. Documentation & Tutorials
- Writing new Literate.jl tutorials in `docs/examples/`.
- Improving the mathematical primer.
- Providing better examples for general relativity use-cases.

## Testing Your Changes

Before submitting a PR, please ensure:
1. `julia --project=src/julia test/runtests.jl` passes.
2. `uv run pytest` passes (if you have the oracle set up).
3. `just docs` builds the documentation without errors.
