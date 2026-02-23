# sxAct — xAct Migration Experiments

Experiments in migrating [xAct](http://xact.es/) (a Wolfram Language tensor algebra library) to open-source ecosystems (Julia, Python).

The core workflow: run xAct computations via a Dockerized Wolfram Engine, capture results, and build a Python testing layer that can validate equivalent open-source implementations.

## Quick Start

**Prerequisites:** Docker, Python ≥ 3.10, [uv](https://docs.astral.sh/uv/)

```bash
# Install Python dependencies
uv sync

# Start the Wolfram/xAct oracle server
docker compose up -d

# Run tests (unit tests only, no oracle required)
uv run pytest tests/ -m "not oracle and not slow"

# Run full integration tests (requires oracle)
uv run pytest tests/integration/
```

See [SETUP.md](SETUP.md) for first-time setup (Wolfram Engine activation, Docker configuration).

## Architecture

```
sxAct/
├── src/sxact/
│   ├── oracle/          # HTTP client for the Wolfram/xAct Docker service
│   │   ├── client.py    # OracleClient: sends expressions, gets results
│   │   └── result.py    # OracleResult: typed wrapper for xAct responses
│   ├── normalize/       # Expression normalization pipeline
│   │   └── pipeline.py  # Canonicalize xAct output for comparison
│   └── compare/         # Comparison and sampling utilities
│       ├── comparator.py  # Assert equivalence between implementations
│       └── sampling.py    # Generate test expressions
├── tests/
│   ├── oracle/          # Unit tests for oracle client/result
│   ├── normalize/       # Unit tests for normalization pipeline
│   ├── compare/         # Unit tests for comparator and sampling
│   └── integration/     # End-to-end tests against live oracle
├── notebooks/           # Wolfram/Python example scripts
├── resources/xAct/      # xAct 1.2.0 library (Wolfram packages)
├── docker-compose.yml   # Wolfram Engine + oracle server
└── pyproject.toml       # Python package config (uv)
```

## Key Components

### Oracle (`src/sxact/oracle/`)

Thin HTTP client to a Dockerized Wolfram Engine running xAct. Sends tensor expressions as strings, returns structured results.

```python
from sxact.oracle import OracleClient

client = OracleClient()
result = client.evaluate("CD[-a][v[b]]")
print(result.output)  # xAct-normalized string
```

### Normalize (`src/sxact/normalize/`)

Pipeline that canonicalizes xAct output (index renaming, sorting, sign normalization) to enable reliable comparison across implementations.

### Compare (`src/sxact/compare/`)

Comparator that asserts two tensor expressions are equivalent after normalization, plus sampling utilities for generating diverse test cases.

## Running Tests

```bash
# Fast unit tests (no Docker needed)
uv run pytest tests/oracle tests/normalize tests/compare

# Integration tests (oracle Docker must be running)
uv run pytest tests/integration/ -m oracle

# All tests
uv run pytest
```

Test markers:
- `oracle` — requires the Docker oracle server
- `slow` — xAct loads in ~3 min, these tests take time

## xAct Packages Available

Located in `resources/xAct/` (v1.2.0):

| Package | Purpose |
|---------|---------|
| xCore | Core infrastructure |
| xTensor | Tensor algebra (main package) |
| xCoba | Coordinate-based calculations |
| xPert | Perturbation theory |
| xPerm | Permutation handling |
| Spinors | Spinor calculus |
| Invar | Curvature invariants |
| Harmonics | Harmonic analysis |
| xTras | Additional utilities |

## Project Goals

1. **Document xAct capabilities** — build a reference test suite of tensor algebra operations
2. **Validate open-source implementations** — use the oracle to verify Julia/Python ports
3. **Identify migration paths** — evaluate SymPy, Cadabra, Symbolics.jl, etc.
4. **Build prototypes** — implement xAct-equivalent functionality in open-source languages

## Resources

- [xAct Homepage](http://xact.es/) — official documentation
- [Wolfram Engine](https://www.wolfram.com/engine/) — free for non-production use
- [Wolfram Client for Python](https://reference.wolfram.com/language/WolframClientForPython/)
- [MathLink.jl](https://github.com/JuliaInterop/MathLink.jl) — Julia ↔ Wolfram bridge
