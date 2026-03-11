---
date: 2026-03-11T10:40:48-03:00
git_commit: c41a519
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-00d, sxAct-2ut
status: handoff
---

# Handoff: Basis/Frame support complete, xCoba unblocked

## Context

This session focused on advancing the xAct migration. Two issues were resolved:

1. **sxAct-2ut** (P1) — "Bundle subcomponents into xAct.jl meta-package" was verified complete (all 5 acceptance criteria met) and closed.
2. **sxAct-00d** (P2) — "xTensor: Implement Basis and Frame support" was implemented from scratch. This adds `def_basis!` and `def_chart!` to XTensor.jl, providing the foundation layer that xCoba (coordinate transformations and component maps) depends on.

## Current Status

### Completed
- [x] sxAct-2ut: xAct.jl meta-package bundling (verified already complete, closed)
- [x] sxAct-00d: Basis/Frame support — `BasisObj`, `ChartObj`, `def_basis!`, `def_chart!`
- [x] All predicates: `BasisQ`, `ChartQ`, `VBundleOfBasis`, `BasesOfVBundle`, `CNumbersOf`, `PDOfBasis`, `ManifoldOfChart`, `ScalarsOfChart`
- [x] `CovDQ` updated to recognize parallel derivatives from bases
- [x] `ValidateSymbolInSession` checks basis/chart name collisions
- [x] Adapter: `DefBasis` and `DefChart` actions in `julia_stub.py`
- [x] Schema: `DefBasis`/`DefChart` arg definitions in `test-schema.json`
- [x] 62 new Julia unit tests + 13 new TOML tests, all passing
- [x] Oracle snapshots generated for basis_frame tests

### Not In Progress
- No issues currently in_progress

### Ready to Pick Up
- **sxAct-eex** (P2): xCoba — Coordinate Transformations (NOW UNBLOCKED by Basis/Frame)
- **sxAct-kzh** (P2): xCoba — Component Maps / CTensor (NOW UNBLOCKED by Basis/Frame)
- **sxAct-x8q** (P2): Invar — Multi-term symmetry engine (NOT session-sized, 5-8 weeks)
- **sxAct-3et** epic: Docs overhaul (leaf tasks: sxAct-kx9 dir refactor, sxAct-bh8 Project.toml)

## Critical Files

> These are the MOST IMPORTANT files to understand for continuation

1. `src/julia/XTensor.jl:125-162` — `BasisObj` and `ChartObj` struct definitions
2. `src/julia/XTensor.jl:690-795` — `def_basis!` and `def_chart!` implementations
3. `src/julia/XTensor.jl:293-297` — `BasisQ`, `ChartQ`, updated `CovDQ` predicates
4. `src/julia/XTensor.jl:330-380` — Basis accessor functions (`VBundleOfBasis`, etc.)
5. `src/sxact/adapter/julia_stub.py:365-393` — `_def_basis` and `_def_chart` adapter methods
6. `src/sxact/runner/schemas/test-schema.json:362-410` — DefBasis/DefChart arg schemas
7. `tests/xtensor/basis_frame.toml` — 13 TOML tests covering basis/chart functionality
8. `src/julia/tests/test_xtensor.jl:753-928` — 62 Julia unit tests for basis/frame

## Recent Changes

> Files modified in this session

- `src/julia/XTensor.jl` — Added BasisObj/ChartObj structs, registries, def_basis!, def_chart!, predicates, accessors, updated reset_state!/ValidateSymbolInSession/CovDQ/MemberQ
- `src/julia/tests/test_xtensor.jl` — 7 new test sets: DefBasis, DefBasis validation, DefChart, DefChart validation, Basis/Chart reset, ValidateSymbolInSession collision, String overloads
- `src/sxact/adapter/julia_stub.py` — Added DefBasis/DefChart to _XTENSOR_ACTIONS, dispatch, and handler methods
- `src/sxact/adapter/base.py` — Added DefBasis/DefChart to supported_actions()
- `src/sxact/runner/schemas/test-schema.json` — Added DefBasis/DefChart to actionName enum, actionArgs anyOf, and args definitions
- `tests/xtensor/basis_frame.toml` — New test file (13 tests)
- `oracle/xtensor/basis_frame/*.json` — 11 new oracle snapshot files

## Key Learnings

> Important discoveries that affect future work

1. **DefChart mirrors Wolfram's DefChart→DefBasis pattern**
   - In Wolfram xAct, `DefChart` internally calls `DefBasis` with `is_chart=true`
   - Our implementation follows the same pattern: `def_chart!` calls `def_basis!` then overlays chart metadata
   - See `resources/xAct/xCoba/xCoba.m:2586-2587` for the Wolfram reference

2. **CovDQ now has dual sources**
   - Previously: only checked `_metrics` (metric covariant derivatives)
   - Now: also checks parallel derivatives from bases via `any(b -> b.parallel_deriv == s, values(_bases))`
   - This is important for xCoba where coordinate derivatives are CovDs

3. **Coordinate scalars are rank-0 tensors**
   - `def_chart!` registers each coordinate scalar (e.g. `:t`, `:r`) as a `TensorObj` with empty slots
   - This matches Wolfram's behavior where coordinate scalars are `xTensorQ` objects

4. **Migration epics have infrastructure gaps beyond code**
   - xCore/xPerm/xTensor epics (k0a/rl6/ctx) are "BLOCKED" in beads but code is largely done
   - Remaining gaps: (a) public Python API, (b) xPerm property tests, (c) xTensor benchmarks
   - These are tracked implicitly in epic acceptance criteria but not as separate beads issues

5. **Oracle snapshots for axiom tests**
   - Even `oracle_is_axiom=true` tests need snapshot JSON files
   - Assert tests: `normalized_output = "True"`
   - Evaluate tests: `normalized_output = <expected value>`
   - Hash: `sha256:hashlib.sha256(json.dumps({"normalized_output":..., "properties":...}, sort_keys=True).encode()).hexdigest()[:12]`

## Open Questions

- [ ] Should xCoba coordinate transformations (sxAct-eex) implement full Jacobian machinery or start with simpler basis-change matrices?
- [ ] Should CTensor (sxAct-kzh) store components as Julia Arrays or use a custom sparse structure?
- [ ] The migration epics (k0a, rl6, ctx) have acceptance criteria for public Python API, property tests, and benchmarks — should these be broken into separate issues?

## Next Steps

> Prioritized actions for next session

1. **xCoba: Coordinate Transformations** (sxAct-eex) [Priority: HIGH]
   - Now unblocked by Basis/Frame support
   - Implement `BasisChange`, `SetBasisChange`, `ChangeBasis`
   - Reference: `resources/xAct/xCoba/xCoba.m:369-431` for Wolfram implementation

2. **xCoba: Component Maps / CTensor** (sxAct-kzh) [Priority: HIGH]
   - Implement `CTensor` struct for storing tensor components in a basis
   - `ComponentArray`, `TableOfComponents`, `BasisExpand`
   - Reference: `resources/xAct/xCoba/xCoba.m` (search for CTensor)

3. **Close migration epics** [Priority: MEDIUM]
   - Create sub-issues for remaining acceptance criteria gaps:
     - Public Python API module (`sxact.api`)
     - xPerm property tests (group law verification)
     - xTensor/xPerm benchmarks (with Wolfram baseline)
   - Close k0a/rl6/ctx epics once sub-issues are tracked

4. **Docs overhaul** [Priority: LOW for now]
   - sxAct-kx9: Refactor docs/ dir structure
   - sxAct-bh8: Init Julia project for docs
   - User deferred this in favor of migration work

## Artifacts

**New files:**
- `tests/xtensor/basis_frame.toml`
- `oracle/xtensor/basis_frame/` (11 JSON snapshot files)

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
| xTensor TOML | 170 | All pass (13 new) |
| Julia XTensor unit | 244 | All pass (62 new) |
| Python runner | 550 | All pass (17 skipped) |

## References

- Wolfram xCoba source: `resources/xAct/xCoba/xCoba.m` (DefBasis: L318-431, DefChart: L2538-2600)
- Doc strategy spec: `specs/2026-03-09-documentation-strategy.md`
- Migration plan: `specs/XACT_LIBRARIES_MIGRATION_PLAN.md`
- Previous handoff: `handoffs/2026-03-10_18-00-12_ibp-vard-complete.md`
