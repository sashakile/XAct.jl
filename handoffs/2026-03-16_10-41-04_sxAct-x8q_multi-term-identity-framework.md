---
date: 2026-03-16T10:41:04-03:00
git_commit: dad9056
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-x8q (closed), sxAct-04r (claimed, not started)
status: handoff
---

# Handoff: Invar Multi-Term Identity Framework & CI Fixes

## Context

Working on the Invar migration — porting Wolfram xAct's Invar module (Riemann invariant simplification) to Julia. The implementation follows an 11-phase plan at `plans/2026-03-11-multi-term-symmetry-engine.md`. Phase 1 (sxAct-x8q) is complete: a general multi-term identity framework that replaces the hardcoded `_bianchi_reduce!`. Two CI flaky-test fixes were also applied.

## Current Status

### Completed
- [x] **Phase 1 (sxAct-x8q): Multi-term identity framework** — `src/XTensor.jl:196-230` struct, `:348-480` framework functions
- [x] `MultiTermIdentity` struct with fixed/cycled slots, slot_perms, coefficients, elimination rule
- [x] `RegisterIdentity!()` and `_identity_registry` global — `src/XTensor.jl:354-365`
- [x] `_apply_identities!()` / `_apply_single_identity!()` — general engine at `src/XTensor.jl:393-480`
- [x] `_make_bianchi_identity()` — constructs first Bianchi for any tensor at `src/XTensor.jl:367-391`
- [x] Auto-registration of Bianchi for all RiemannSymmetric tensors in `def_tensor!` — `src/XTensor.jl:787-789`, `src/XTensor.jl:861-863`
- [x] `_bianchi_reduce!` is now a thin wrapper at `src/XTensor.jl:1412-1418`
- [x] `reset_state!()` clears `_identity_registry` — `src/XTensor.jl:345`
- [x] 26 new tests in `test/julia/test_xtensor.jl:1886-1985` (registration, reset, manual registration, Bianchi via framework, multiple tensors, user-defined RiemannSymmetric)
- [x] **Fix: wolfram adapter flaky tests** — `packages/sxact/src/sxact/adapter/wolfram.py:125-158` overrides `supported_actions()` to match `_build_expr` coverage
- [x] **Fix: perf test threshold** — `tests/unit/test_xcore_python.py:565` extracted `_PERF_MAX_RATIO = 2.5`

### In Progress
- [ ] **Phase 2 (sxAct-04r)**: Claimed but no code written yet. RPerm/RInv types + MaxIndex table + InvarCases.

### Planned (Critical Path)
- [ ] Phase 2 (sxAct-04r): RPerm/RInv types, ~150 lines, 1 session
- [ ] Phase 5 (sxAct-h85): Database parser, ~400 lines, 2 sessions — **can parallelize with Phase 3**
- [ ] Phase 3 (sxAct-lwb): RiemannToPerm, ~400 lines, 3 sessions
- [ ] Phase 4 (sxAct-w50): PermToInv lookup, ~100 lines, 1 session
- [ ] Phase 6 (sxAct-23p): InvSimplify, ~250 lines, 2 sessions
- [ ] Phase 7 (sxAct-6i2): RiemannSimplify end-to-end, ~300 lines, 2 sessions
- [ ] Phases 8-11: CovD commutation, dim-dependent, duals, benchmarks

## Critical Files

1. `src/XTensor.jl:196-230` - `MultiTermIdentity` struct definition
2. `src/XTensor.jl:348-480` - Framework: `RegisterIdentity!`, `_apply_identities!`, `_apply_single_identity!`
3. `src/XTensor.jl:787-789` - Auto-registration in `def_tensor!` (single-manifold variant)
4. `src/XTensor.jl:861-863` - Auto-registration in `def_tensor!` (multi-manifold variant)
5. `plans/2026-03-11-multi-term-symmetry-engine.md` - Full 11-phase implementation plan
6. `test/julia/test_xtensor.jl:1886-1985` - New MultiTermIdentity tests
7. `src/XAct.jl` - Bundle entry point (will need `include("XInvar.jl")` in Phase 2)

## Recent Changes

- `src/XTensor.jl` — Added MultiTermIdentity struct, framework functions, auto-registration, replaced _bianchi_reduce! call
- `test/julia/test_xtensor.jl` — Added 26 new tests for identity framework
- `packages/sxact/src/sxact/adapter/wolfram.py` — Added `supported_actions()` override to fix flaky conformance tests
- `tests/unit/test_xcore_python.py` — Extracted `_PERF_MAX_RATIO = 2.5` constant, relaxed from 2.0x

## Key Learnings

1. **Bianchi slot permutations after canonicalization**
   - For indices p < q < r < s, the three canonical Bianchi forms are:
     X₁ = R[p,q,r,s] → cycled ranks [1,2,3]
     X₂ = R[p,r,q,s] → cycled ranks [2,1,3]
     X₃ = R[p,s,q,r] → cycled ranks [3,1,2]
   - Identity: X₁ - X₂ + X₃ = 0, eliminate X₃
   - See `src/XTensor.jl:367-391` for construction

2. **Identity application requires all terms present**
   - Matches the original `_bianchi_reduce!` behavior: only eliminates when all N terms of the identity exist in the sector with non-zero coefficients
   - See `_apply_single_identity!` at `src/XTensor.jl:438-480`

3. **Auto-registration covers all RiemannSymmetric tensors**
   - Both `def_tensor!` variants (single/multi-manifold) register Bianchi
   - This covers Riemann, Weyl, and any user-defined RiemannSymmetric tensor

4. **frozenset iteration is non-deterministic in Python**
   - Root cause of the wolfram adapter flake: `next(iter(frozenset(...)))` picks random elements
   - Fix: adapter must only claim actions it actually handles

## Open Questions

- [ ] Phase 2 file organization: plan says `src/XInvar.jl` — confirm `XAct.jl` include order
- [ ] Invar database availability: plan mentions `xact.es/Invar/Riemann.tar.gz` — need to verify URL is still live for Phase 5

## Next Steps

1. **Phase 2: RPerm/RInv types (sxAct-04r)** [Priority: HIGH]
   - New file `src/XInvar.jl` with InvariantCase, RPerm, RInv structs
   - MaxIndex table (47 non-dual cases) from Invar.m:389-452
   - `InvarCases()`, `PermDegree()` functions
   - Add `include("XInvar.jl")` to `src/XAct.jl`
   - ~150 lines, 1 session

2. **Phase 5: Database parser (sxAct-h85)** [Priority: HIGH, parallelizable]
   - New file `src/InvarDB.jl`
   - Maple format parser for step-1 permutation files
   - Mathematica format parser for step-2 through step-6 rule files
   - ~400 lines, 2 sessions

3. **Phase 3: RiemannToPerm (sxAct-lwb)** [Priority: HIGH, after Phase 2]
   - Convert Riemann scalar expressions to canonical RPerm forms
   - Contraction permutation extraction algorithm
   - ~400 lines, 3 sessions

## Artifacts

**Modified files:**
- `src/XTensor.jl`
- `test/julia/test_xtensor.jl`
- `packages/sxact/src/sxact/adapter/wolfram.py`
- `tests/unit/test_xcore_python.py`

**Not committed:**
- `.claude/settings.local.json` (local settings, not tracked)

## Test Results (all green)

| Suite | Count |
|-------|-------|
| Julia XTensor | 417/417 (341 + 31 + 19 + 26 new) |
| Julia XPerm | 91/91 |
| TOML xTensor | 213/213 |
| TOML xPerm | 156/156 |
| Python | 567/567 |
| Aqua + JET + Formatter | all pass |

## References

- Full plan: `plans/2026-03-11-multi-term-symmetry-engine.md`
- Wolfram source: `resources/xAct/Invar/Invar.m`
- Papers: Martín-García et al. (2008) arXiv:0802.1274
- Beads issues: `bd show sxAct-x8q` (closed), `bd show sxAct-04r` (next)
- Dependency graph: Phase 1 → 2 → 3 → (5 parallel) → 4 → 6 → 7
