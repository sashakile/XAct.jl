# Historical specs

This directory contains pre-OpenSpec design documents, research notes, schemas, and migration plans.

## Status

These files are **historical design artifacts**, not the authoritative source of truth for active changes.

Use them for:
- architectural background
- rationale behind older implementation decisions
- historical migration context
- schema/reference material that is still directly consumed by tooling

Do **not** assume every statement here reflects current repository state.

## Authoritative sources today

- **Active/proposed changes:** `openspec/changes/`
- **Current implemented behavior captured in OpenSpec:** `openspec/specs/`
- **Current code and tests:** `src/`, `packages/`, `test/`, `tests/`
- **Tracked work:** `bd` issues

## Important caveats

- Some documents here predate package publication in Julia registries / PyPI.
- Some documents discuss adjacent projects (`elegua`, `chacana`, `yachay`) whose current authoritative specs live in their own repositories.
- Some items remain useful only as snapshots of intent from a specific date.

When updating code or docs, prefer adding new OpenSpec changes/specs instead of editing historical files unless you are explicitly curating repository history.
