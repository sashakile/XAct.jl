---
date: 2026-03-16T12:32:50-03:00
git_commit: 7f52a0b
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-04r (closed), sxAct-lwb (closed), sxAct-h85 (closed), sxAct-w50 (next)
status: handoff
---

# Handoff: Invar Phases 2, 3, 5 Complete — Types, RiemannToPerm, Database Parser

## Context

Continuing the Invar migration — porting Wolfram xAct's Invar module (Riemann invariant simplification) to Julia. The 11-phase plan is at `plans/2026-03-11-multi-term-symmetry-engine.md`. This session completed Phases 2, 3, and 5 (3 and 5 ran in parallel via worktree agents). The core pipeline is taking shape: types → string parsing → permutation extraction → database loading.

## Current Status

### Completed
- [x] **Phase 1 (sxAct-x8q)**: Multi-term identity framework — `src/XTensor.jl:196-480`
- [x] **Phase 2 (sxAct-04r)**: InvariantCase/RPerm/RInv types, MaxIndex tables, InvarCases — `src/XInvar.jl:33-337`
- [x] **Phase 3 (sxAct-lwb)**: RiemannToPerm/PermToRiemann pipeline — `src/XInvar.jl:339-1232`
- [x] **Phase 5 (sxAct-h85)**: InvarDB.jl database parser + lazy loading — `src/InvarDB.jl`, `src/XInvar.jl:1234-1263`

### In Progress
- [ ] **Phase 4 (sxAct-w50)**: PermToInv lookup — claimed, not started

### Planned (Critical Path)
- [ ] Phase 4 (sxAct-w50): PermToInv/InvToPerm lookup, ~100 lines, 1 session
- [ ] Phase 6 (sxAct-23p): InvSimplify 6-level pipeline, ~250 lines, 2 sessions
- [ ] Phase 7 (sxAct-6i2): RiemannSimplify end-to-end, ~300 lines, 2 sessions
- [ ] Phases 8-11: CovD commutation, dim-dependent, duals, benchmarks

## Critical Files

1. `src/XInvar.jl:33-337` — Phase 2: types, MaxIndex tables, InvarCases enumeration
2. `src/XInvar.jl:339-1087` — Phase 3: string parsing, contraction perm extraction, canonicalization
3. `src/XInvar.jl:1089-1232` — Phase 3: PermToRiemann + curvature relations
4. `src/XInvar.jl:1234-1263` — Lazy DB loading globals
5. `src/InvarDB.jl` — Phase 5: Maple/Mathematica format parsers, LoadInvarDB
6. `src/xAct.jl` — Bundle; includes XInvar.jl, reset_state! calls _reset_invar_db!
7. `test/julia/test_xinvar.jl` — 622 tests across all three phases
8. `plans/2026-03-11-multi-term-symmetry-engine.md` — Full 11-phase implementation plan

## Recent Changes

- `src/XInvar.jl` — New module: types (Phase 2), RiemannToPerm pipeline (Phase 3), lazy loading
- `src/InvarDB.jl` — New file: database parsers (Phase 5)
- `src/xAct.jl` — Added `include("XInvar.jl")`, `@reexport using .XInvar`, `_reset_invar_db!()` in reset
- `test/julia/test_xinvar.jl` — New file: 622 tests

## Key Learnings

1. **Contraction perm canonicalization uses brute-force enumeration**
   - Enumerates all 8^n Riemann symmetry configs × block permutations
   - Picks lexicographically minimal permutation
   - Acceptable for n ≤ 9 Riemanns (practical GR limit)
   - See `src/XInvar.jl:944-1021` (`_canonicalize_contraction_perm`)

2. **CovD index slots precede Riemann slots in each factor**
   - `CD[-e][RiemannCD[-a,-b,-c,-d]]` → slots: [e, a, b, c, d] (5 slots)
   - Slot assignment is left-to-right across factors
   - See `src/XInvar.jl:735-787` (`_extract_contraction_perm`)

3. **Ricci-to-Riemann expansion uses fresh dummy indices**
   - `_FRESH_INDEX_POOL` provides `xa, xb, ...` names to avoid collisions
   - `RicciCD[-a,-b]` → `RiemannCD[xa,-a,-xa,-b]` (contracted slots 1&3)
   - `RicciScalarCD[]` → `RiemannCD[xa,xb,-xa,-xb]`
   - See `src/XInvar.jl:661-692`

4. **InvarCases count is 48 (not 47 as stated in earlier handoffs)**
   - Orders 2,4,6,8,10,12,14 → 1+2+4+7+12+21+1 = 48 non-dual cases
   - MaxIndex has 50 entries (48 + degree-8 and degree-9 algebraic)
   - InvarDualCases: 15 cases (orders 2-10)

5. **InvarDB parser handles two formats**
   - Maple (step-1): `RInv[{0,0},1] := [[2,1],[4,3],[6,5],[8,7]];` → cycle notation → images
   - Mathematica (steps 2-6): `RInv[{0,0},3] -> RInv[{0,0},1] - RInv[{0,0},2]` → substitution rules
   - Missing files produce warnings, not errors

## Open Questions

- [ ] Invar database availability: need to verify xact.es/Invar/Riemann.tar.gz is still live
- [ ] Phase 4 dispatch cache: should use `Dict{Vector{Int}, Dict{Vector{Int}, Int}}` keyed by case for O(1) perm→index lookup
- [ ] Performance of brute-force canonicalization at degree 7 (16532 invariants, 28 index slots)

## Next Steps

1. **Phase 4: PermToInv lookup (sxAct-w50)** [Priority: HIGH]
   - `PermToInv(rperm)` — looks up invariant index from loaded DB
   - `InvToPerm(rinv)` — reverse lookup
   - Dispatch cache for O(1) lookup
   - ~100 lines, 1 session

2. **Phase 6: InvSimplify (sxAct-23p)** [Priority: HIGH, after Phase 4]
   - 6-level simplification pipeline using database rules
   - Levels: cyclic → Bianchi → CovD commute → dim-dependent → dual
   - ~250 lines, 2 sessions

3. **Phase 7: RiemannSimplify (sxAct-6i2)** [Priority: HIGH, after Phase 6]
   - End-to-end: expr → RiemannToPerm → PermToInv → InvSimplify → PermToRiemann
   - Adapter action + TOML tests
   - ~300 lines, 2 sessions

## Artifacts

**New files:**
- `src/XInvar.jl`
- `src/InvarDB.jl`
- `test/julia/test_xinvar.jl`

**Modified files:**
- `src/xAct.jl`

## Test Results (all green)

| Suite | Count |
|-------|-------|
| Julia XInvar | 622/622 |
| Julia XTensor | 417/417 |
| Julia XPerm | 91/91 |
| Python | 567/567 |

## References

- Full plan: `plans/2026-03-11-multi-term-symmetry-engine.md`
- Wolfram source: `resources/xAct/Invar/Invar.m`
- Papers: Martin-Garcia et al. (2008) arXiv:0802.1274
- Dependency graph: Phase 1 → 2 → 3 → (5 parallel) → 4 → 6 → 7
- Beads: `bd show sxAct-w50` (next), `bd show sxAct-23p` (Phase 6)
