---
date: 2026-03-16T15:20:32-03:00
git_commit: 7fe6ec1
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-1gx (Phase 11, remaining)
status: handoff
---

# Handoff: Invar Phases 1-10 Complete — Full Pipeline Ready

## Context

Porting Wolfram xAct's Invar module (Riemann invariant simplification) to Julia. The 11-phase plan is at `plans/2026-03-11-multi-term-symmetry-engine.md`. Phases 1-10 are now complete in a single marathon session. Only Phase 11 (validation benchmarks) remains.

## Current Status

### Completed (all in this session)
- [x] **Phase 1 (sxAct-x8q)**: Multi-term identity framework — `src/XTensor.jl`
- [x] **Phase 2 (sxAct-04r)**: InvariantCase/RPerm/RInv types, MaxIndex — `src/XInvar.jl`
- [x] **Phase 3 (sxAct-lwb)**: RiemannToPerm/PermToRiemann pipeline — `src/XInvar.jl`
- [x] **Phase 4 (sxAct-w50)**: PermToInv/InvToPerm lookup + dispatch cache — `src/XInvar.jl`
- [x] **Phase 5 (sxAct-h85)**: InvarDB database parser (Maple + Mathematica) — `src/InvarDB.jl`
- [x] **Phase 6 (sxAct-23p)**: InvSimplify 6-level pipeline — `src/XInvar.jl`
- [x] **Phase 7 (sxAct-6i2)**: RiemannSimplify end-to-end — `src/XInvar.jl`
- [x] **Phase 8 (sxAct-6e3)**: SortCovDs + RicciIdentity registration — `src/XTensor.jl`
- [x] **Phase 9 (sxAct-sci)**: Dim-dependent identities (already done by Phases 5+6)
- [x] **Phase 10 (sxAct-mbj)**: Dual invariant routing — `src/XInvar.jl`

### Remaining
- [ ] **Phase 11 (sxAct-1gx)**: Validation benchmarks — blocked on nothing, ready to start

## Critical Files

1. `src/XInvar.jl` — Core module: types, RiemannToPerm, PermToInv, InvSimplify, RiemannSimplify, dual routing
2. `src/InvarDB.jl` — Database parser: Maple/Mathematica format, LoadInvarDB, InvarDB struct
3. `src/XTensor.jl` — SortCovDs, CommuteCovDs, MultiTermIdentity framework
4. `src/xAct.jl` — Bundle: includes XInvar, reset_state! clears all caches
5. `test/julia/test_xinvar.jl` — 771 tests (types, parsing, conversion, DB, simplification, duals)
6. `test/julia/test_xtensor.jl` — 441 tests (including 24 SortCovDs)
7. `plans/2026-03-11-multi-term-symmetry-engine.md` — Full 11-phase plan

## Key Architecture

### Pipeline: RiemannSimplify
```
expr (string) → RiemannToPerm → PermToInv → InvSimplify → InvToPerm → PermToRiemann → string
```

### Module structure
```
xAct.jl
├── XCore.jl
├── XTensor.jl (includes XPerm.jl)
│   ├── MultiTermIdentity framework
│   ├── SortCovDs / CommuteCovDs
│   └── RicciIdentity auto-registration
└── XInvar.jl (includes InvarDB.jl)
    ├── Types: InvariantCase, RPerm, RInv
    ├── Tables: MaxIndex (50), MaxDualIndex (17), InvarCases (48), InvarDualCases (15)
    ├── Phase 3: String parsing, contraction perm extraction, canonicalization
    ├── Phase 4: PermToInv/InvToPerm with dispatch cache
    ├── Phase 5: InvarDB parser (Maple + Mathematica)
    ├── Phase 6: InvSimplify (6 levels: cyclic/Bianchi/CovD/dim-dep/dual)
    ├── Phase 7: RiemannSimplify (end-to-end)
    └── Phase 10: Dual routing (_dual_perm_dispatch, n_epsilon checks)
```

### Database flow
```
LoadInvarDB(dbdir) → InvarDB struct
  .perms: case → (index → perm)
  .dual_perms: case → (index → perm)
  .rules[step]: case → (dep_index → [(ind_index, coeff), ...])
  .dual_rules[step]: same for duals
```

## Test Results

| Suite | Count |
|-------|-------|
| Julia XInvar | 771/771 |
| Julia XTensor | 441/441 |
| Julia XPerm | 91/91 |
| Python | 567/567 |

## Key Learnings

1. **Contraction perm canonicalization**: brute-force 8^n × block perms, lex-minimal selection. Acceptable for n ≤ 9 Riemanns.
2. **CovD slot assignment**: CovD indices precede Riemann indices per factor. `CD[-e][R[-a,-b,-c,-d]]` → slots [e,a,b,c,d].
3. **Dual routing**: n_epsilon=0 → db.perms/rules, n_epsilon=1 → db.dual_perms/dual_rules. dim=4 required for duals.
4. **SortCovDs**: bubble-sort on CovD indices, each swap generates Riemann correction terms via CommuteCovDs.
5. **InvarCases count**: 48 non-dual (not 47), 15 dual. MaxIndex has 50 entries (48 + degree 8,9).
6. **Phase 9 was already done**: InvSimplify level 5 + DB parser step-5 = complete dim-dependent handling.

## Next Steps

1. **Phase 11: Validation benchmarks (sxAct-1gx)** [Priority: HIGH]
   - TOML tests: `tests/xtensor/riemann_invariants.toml`
   - Kretschner, Ricci square, cubic invariant classification
   - Degree 2-7 independent invariant counts vs MaxIndex
   - Performance: degree-2 < 10ms, degree-4 < 100ms
   - Round-trip stability tests
   - ~200 lines, needs real Invar database files

2. **Database acquisition** [Priority: HIGH for Phase 11]
   - Need `xact.es/Invar/Riemann.tar.gz` — verify URL still works
   - Or bundle low-order cases as Julia source

## References

- Full plan: `plans/2026-03-11-multi-term-symmetry-engine.md`
- Wolfram source: `resources/xAct/Invar/Invar.m`
- Beads: `bd show sxAct-1gx` (Phase 11, only remaining)
