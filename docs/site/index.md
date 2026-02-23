# sxAct

Experiments in migrating [xAct](http://xact.es/) — a Wolfram Language tensor algebra library — to open-source ecosystems (Julia, Python).

## What is this?

**xAct** is a powerful tensor algebra and differential geometry package for Wolfram Language. This project builds tooling to:

1. Run xAct computations via a Dockerized Wolfram Engine (the "oracle")
2. Capture and normalize xAct output
3. Validate equivalent open-source implementations against the oracle

## Quick Start

```bash
# Install dependencies
uv sync

# Start the oracle server
docker compose up -d

# Run tests
uv run pytest tests/ -m "not oracle and not slow"
```

See [Installation](installation.md) for full setup, or [Getting Started](getting-started.md) for your first computation.

## Architecture

```
Oracle (Wolfram/xAct) → Normalize → Compare
```

The [`oracle`](api/oracle.md) module communicates with a running Wolfram Engine.
The [`normalize`](api/normalize.md) module canonicalizes xAct expressions.
The [`compare`](api/compare.md) module asserts equivalence between implementations.
