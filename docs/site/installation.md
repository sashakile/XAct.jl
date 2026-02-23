# Installation

## Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| Docker | 20.10+ | Engine + Compose |
| Python | 3.10+ | Managed via uv |
| [uv](https://docs.astral.sh/uv/) | 0.4+ | Python package manager |

No local Wolfram Engine or Julia installation required — everything Wolfram-related runs in Docker.

## 1. Clone the repository

```bash
git clone git@github.com:sashakile/sxAct.git
cd sxAct
```

## 2. Install Python dependencies

```bash
uv sync
```

For development (tests, type checking):

```bash
uv sync --extra dev
```

For building documentation:

```bash
uv sync --extra docs
```

## 3. Activate the Wolfram Engine (first time only)

The Wolfram Engine requires a one-time license activation. You'll need a free
[Wolfram ID](https://account.wolfram.com/auth/create) (free for non-production use).

```bash
docker compose run --rm wolfram wolframscript -activate
```

Follow the prompts. The license is stored in the `wolfram-config` Docker volume and persists across container restarts.

!!! note
    This only needs to be done once. The license is tied to the machine's hardware fingerprint.

## 4. Start the oracle server

The oracle server is a Wolfram Engine process running xAct, exposed over HTTP on port 8765.

```bash
docker compose up -d oracle
```

Wait for the health check to pass (~30–60 seconds for xAct to load):

```bash
docker compose ps         # Status: healthy
curl http://localhost:8765/health
```

## 5. Verify the installation

```bash
# Unit tests (no oracle required, fast)
uv run pytest tests/oracle tests/normalize tests/compare

# Integration tests (oracle must be running)
uv run pytest tests/integration/

# Full suite
uv run pytest
```

Expected output: all unit tests pass in a few seconds; integration tests take longer
due to xAct initialization (~3 minutes on first load).

## Troubleshooting

### Wolfram Engine not activated

```
Error: No valid license found
```

Re-run the activation step:

```bash
docker compose run --rm wolfram wolframscript -activate
```

### xAct not found in container

Confirm the `resources/xAct/` directory exists and contains xAct packages:

```bash
ls resources/xAct/
# Should show: xCore/ xTensor/ xCoba/ xPert/ ...
```

The directory is mounted read-only at `/opt/xAct` inside the container.

### Oracle not responding

Check that the oracle container started and passed its health check:

```bash
docker compose logs oracle
docker compose ps oracle
```

If the container is unhealthy, the most common cause is xAct failing to load — check the logs for Wolfram errors.

### Port 8765 already in use

Edit `docker-compose.yml` to change the host port:

```yaml
ports:
  - "8766:8765"   # Change 8766 to any free port
```

Then update the oracle client base URL accordingly.
