# Contributing to sxAct

## Setup

**Prerequisites:** Docker, Python ≥ 3.10, [uv](https://docs.astral.sh/uv/)

```bash
# Install all dependencies including dev extras
uv sync --extra dev

# Start the oracle server (needed for integration tests)
docker compose up -d
```

See [SETUP.md](SETUP.md) for first-time Wolfram Engine activation.

## Running Tests

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
- `slow` — these take several minutes due to xAct initialization time

## Code Style

- **Type hints** on all public functions (enforced by mypy in strict mode)
- **No external dependencies** beyond what's in `pyproject.toml` — keep the package lean
- Tests live in `tests/` mirroring the `src/sxact/` structure

## Project Structure

New functionality generally goes in one of three modules:

| Module | Purpose |
|--------|---------|
| `sxact.oracle` | Communication with the Wolfram/xAct backend |
| `sxact.normalize` | Canonicalizing xAct expression strings |
| `sxact.compare` | Asserting equivalence between implementations |

## Workflow

This repo uses a local-only git workflow (no remote pushes). Changes are tracked via [beads](https://github.com/sk/beads) for issue management.

```bash
# Check available work
bd ready

# Claim an issue
bd update <id> --status=in_progress

# Close when done
bd close <id>
```
