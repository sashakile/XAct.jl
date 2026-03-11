# Contributing to xAct.jl

This repository contains both the `xAct.jl` Julia package and the `sxact-py` verification framework.

## 1. Julia Development (xAct.jl)

The Julia source code is located in `src/julia/`.

### Setup
- [Julia 1.10+](https://julialang.org/downloads/)
- Optional: [JuliaExtension](https://marketplace.visualstudio.com/items?itemName=julialang.language-julia) for VS Code.

### Running Julia Tests
```bash
cd src/julia
julia --project=. test/runtests.jl
```

### Code Style
- Use `JuliaFormatter.jl`. A `.JuliaFormatter.toml` is provided in the root.
- Follow the [Blue Style](https://github.com/invenia/BlueStyle) where possible.
- Use `JET.jl` and `Aqua.jl` for static analysis and quality checks (run as part of `runtests.jl`).

---

## 2. Python & Verification Development (sxact-py)

The Python source is in `src/sxact/`.

### Setup
**Prerequisites:** Docker, Python ≥ 3.10, [uv](https://docs.astral.sh/uv/)

```bash
# Install all dependencies including dev extras
uv sync --extra dev

# Start the oracle server (needed for integration tests)
docker compose up -d
```

See [SETUP.md](SETUP.md) for first-time Wolfram Engine activation.

### Running Python Tests
```bash
# Unit tests only (fast, no Docker required)
uv run pytest tests/oracle tests/normalize tests/compare

# Integration tests (oracle must be running)
uv run pytest tests/integration/

# All tests
uv run pytest

# Type checking
uv run mypy src/
```

Test markers:
- `oracle` — requires the Docker oracle server (`docker compose up -d`)
- `slow` — these take several minutes due to xAct initialization time.

---

## 3. Documentation

`xAct.jl` uses [Documenter.jl](https://juliadocs.github.io/Documenter.jl/stable/) for documentation.

### Building
```bash
# Build the documentation
just docs

# Build and serve locally on http://localhost:8000
just serve-docs
```

## 4. Project Structure

| Path | Purpose |
|------|---------|
| `src/julia/` | Native Julia implementation of xAct engines. |
| `src/sxact/` | Python wrapper and verification logic. |
| `tests/` | Multi-tier test suite (Julia, Python, Oracle). |
| `docs/` | Documentation (Julia-centric, built with Documenter.jl). |

## 4. Workflow

This repo uses a local-only git workflow (no remote pushes). Changes are tracked via [beads](https://github.com/sk/beads) for issue management.

```bash
# Check available work
bd ready

# Claim an issue
bd update <id> --status=in_progress

# Close when done
bd close <id>
```
