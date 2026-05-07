---
date: 2026-03-11T15:24:55-03:00
git_commit: bde173f
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-eex, sxAct-kzh
status: handoff
---

# Handoff: xCoba coordinate transformations and CTensor complete

## Context

This session implemented the two core xCoba features that were unblocked by the Basis/Frame work (sxAct-00d) from the previous session. Both features are part of the xCoba migration epic (sxAct-l1w).

1. **sxAct-eex** — Coordinate Transformations: basis change matrices, Jacobians, and slot-wise array transformation.
2. **sxAct-kzh** — CTensor Component Maps: storing, retrieving, and operating on explicit tensor component arrays in given bases.

Both were implemented, reviewed via Rule of 5 Universal, fixed, and committed.

## Current Status

### Completed
- [x] sxAct-eex: `BasisChangeObj`, `set_basis_change!`, `BasisChangeQ`, `BasisChangeMatrix`, `InverseBasisChangeMatrix`, `Jacobian`, `change_basis`
- [x] sxAct-kzh: `CTensorObj`, `set_components!`, `get_components` (with auto-transform), `ComponentArray`, `CTensorQ`, `component_value`, `ctensor_contract`
- [x] Cross-vbundle validation on `set_basis_change!` (RO5U fix)
- [x] Recursive `_nested_list_to_julia` for rank-3+ arrays (RO5U fix)
- [x] `ctensor_contract` `Any` eltype fix for rank>2 (RO5U fix)
- [x] Adapter actions: SetBasisChange, ChangeBasis, GetJacobian, BasisChangeQ, SetComponents, GetComponents, ComponentValue, CTensorQ
- [x] Schema definitions for all 8 new actions
- [x] 34 Julia unit tests for coordinate transforms + 7 TOML tests
- [x] 38 Julia unit tests for CTensor + 8 TOML tests
- [x] Oracle snapshots for all new TOML tests

### Not In Progress
- No issues currently in_progress

### Ready to Pick Up
- **sxAct-dic** (P3): xCoba — DifferentialEquations.jl integration (NOW UNBLOCKED by CTensor)
- **sxAct-x8q** (P2): Invar — Multi-term symmetry engine (NOT session-sized, 5-8 weeks)
- **sxAct-l1w** epic: xCoba migration — 2 of 3 child tasks done (eex ✓, kzh ✓, dic remaining)
- **sxAct-3et** epic: Docs overhaul (leaf tasks: sxAct-kx9, sxAct-bh8)
- **sxAct-ead** epic: Engagement (8 leaf tasks, all P2)

## Critical Files

> These are the MOST IMPORTANT files to understand for continuation

1. `src/julia/XTensor.jl:163-169` — `BasisChangeObj` struct definition
2. `src/julia/XTensor.jl:173-183` — `CTensorObj` struct definition
3. `src/julia/XTensor.jl:3159-3345` — `set_basis_change!`, predicates, accessors, `change_basis`, `_contract_slot`
4. `src/julia/XTensor.jl:3362-3591` — `set_components!`, `get_components` (auto-transform), `ComponentArray`, `CTensorQ`, `component_value`, `ctensor_contract`
5. `src/sxact/adapter/julia_stub.py:40-80` — `_nested_list_to_julia` helper (recursive for N-d)
6. `src/sxact/adapter/julia_stub.py:540-660` — All 8 new adapter handler methods
7. `src/sxact/runner/schemas/test-schema.json:605-796` — Schema defs for all 8 new actions
8. `tests/xtensor/coordinate_transforms.toml` — 7 TOML tests for basis changes
9. `tests/xtensor/ctensor.toml` — 8 TOML tests for component tensors
10. `src/julia/tests/test_xtensor.jl:928-1364` — 72 Julia unit tests for both features

## Recent Changes

> Files modified in this session

- `src/julia/XTensor.jl` — Added BasisChangeObj, CTensorObj, registries, all functions for both features
- `src/julia/tests/test_xtensor.jl` — 72 new tests across ~20 test sets
- `src/sxact/adapter/base.py` — Added 8 actions to `supported_actions()`
- `src/sxact/adapter/julia_stub.py` — Added `_nested_list_to_julia`, 8 handler methods, 8 dispatch entries
- `src/sxact/runner/schemas/test-schema.json` — 8 new action names + arg schemas
- `tests/xtensor/coordinate_transforms.toml` — New test file (7 tests)
- `tests/xtensor/ctensor.toml` — New test file (8 tests)
- `oracle/xtensor/coordinate_transforms/` — 5 oracle snapshot JSON files
- `oracle/xtensor/ctensor/` — 6 oracle snapshot JSON + 6 .wl files

## Key Learnings

> Important discoveries that affect future work

1. **Bidirectional basis change storage**
   - `set_basis_change!(A, B, M)` auto-stores both `(A,B)→M` and `(B,A)→inv(M)` with reciprocal Jacobian
   - Cross-vbundle validation prevents nonsensical changes between bases on different manifolds
   - See `src/julia/XTensor.jl:3185-3205`

2. **CTensor auto-transform via basis changes**
   - `get_components(:g, [:Sph, :Sph])` will find `:g` stored in `[:Cart, :Cart]` and apply basis changes slot-by-slot
   - Uses `change_basis` internally for each slot that differs
   - O(n) search over stored CTensors — acceptable for current scale
   - See `src/julia/XTensor.jl:3435-3465`

3. **`_nested_list_to_julia` must be recursive for rank-3+**
   - Original 2D-only version would silently produce invalid Julia for `[[[1,2],[3,4]],[[5,6],[7,8]]]`
   - Fix uses flatten + reshape with column-major permutation: `permutedims(reshape(flat, reversed_dims...), N:-1:1)`
   - See `src/sxact/adapter/julia_stub.py:64-80`

4. **`ctensor_contract` rank>2 needs explicit numeric eltype**
   - `zeros(Any, ...)` and `zero(Any)` error in Julia
   - Fix: `T = eltype(arr) === Any ? Float64 : eltype(arr)`
   - See `src/julia/XTensor.jl:3559`

5. **RO5U review process found 3 medium-severity issues across both features**
   - eex: Missing cross-vbundle validation
   - kzh: `_nested_list_to_julia` rank-3+ breakage, `ctensor_contract` Any eltype
   - All fixed before commit

## Open Questions

- [ ] xCoba epic (sxAct-l1w) acceptance criteria require Python wrapper, Layer 2 property tests, and Layer 3 benchmarks — should these be broken into separate issues?
- [ ] `GetComponents` schema has `minItems: 1` on `bases`, blocking rank-0 scalar retrieval via TOML — fix if rank-0 TOML tests are needed
- [ ] The `.wl` files generated alongside oracle `.json` snapshots for CTensor tests are unexpected — investigate or ignore?
- [ ] Migration epics (k0a/rl6/ctx/l1w) have acceptance criteria gaps (public Python API, property tests, benchmarks) not tracked as individual issues

## Next Steps

> Prioritized actions for next session

1. **xCoba: DifferentialEquations.jl integration** (sxAct-dic) [Priority: MEDIUM]
   - Now unblocked by CTensor
   - Bridge between sxAct tensor components and Julia's DifferentialEquations.jl
   - P3 priority — may defer in favor of higher-priority work

2. **Invar: Multi-term symmetry engine** (sxAct-x8q) [Priority: HIGH but LARGE]
   - P2, ready, but 5-8 week estimated scope
   - Needs careful planning before starting — not a single-session task

3. **Close xCoba migration epic** (sxAct-l1w) [Priority: MEDIUM]
   - 2 of 3 child tasks done (eex ✓, kzh ✓)
   - Only sxAct-dic (P3) remains; epic could potentially be closed with dic deferred
   - But epic acceptance criteria require Python wrapper + property tests + benchmarks

4. **Docs overhaul** (sxAct-3et) [Priority: LOW]
   - sxAct-kx9: Refactor docs/ directory structure
   - sxAct-bh8: Init Julia project for docs

5. **Engagement epic** (sxAct-ead) [Priority: LOW]
   - 8 leaf tasks for making sxAct accessible to researchers
   - All P2 but deferred in favor of core migration work

## Artifacts

**New files:**
- `tests/xtensor/coordinate_transforms.toml`
- `tests/xtensor/ctensor.toml`
- `oracle/xtensor/coordinate_transforms/` (5 JSON files)
- `oracle/xtensor/ctensor/` (6 JSON + 6 .wl files)

**Modified files:**
- `src/julia/XTensor.jl`
- `src/julia/tests/test_xtensor.jl`
- `src/sxact/adapter/base.py`
- `src/sxact/adapter/julia_stub.py`
- `src/sxact/runner/schemas/test-schema.json`

## Test Results

| Suite | Count | Status |
|-------|-------|--------|
| xPerm TOML | 156 | All pass |
| xTensor TOML | 185 | All pass (7 coord_transforms + 8 ctensor new) |
| Julia XTensor unit | 316 | All pass (34 coord_transforms + 38 ctensor new) |
| Python runner | 550 | All pass (17 skipped) |

## References

- Wolfram xCoba source: `resources/xAct/xCoba/xCoba.m` (BasisChange: L369-431, CTensor: L1227+, SetBasisChange: L1712-1775)
- Previous handoff: `handoffs/2026-03-11_10-40-48_basis-frame-complete.md`
- Migration plan: `specs/XACT_LIBRARIES_MIGRATION_PLAN.md`
