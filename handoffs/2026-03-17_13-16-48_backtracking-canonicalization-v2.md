---
date: 2026-03-17T13:16:48-03:00
git_commit: 7830f3b
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-d7qy
status: handoff
---

# Handoff: Backtracking canonicalization v2 (bounds + dedup)

## Context

`_canonicalize_contraction_perm` finds the lexicographic minimum of a contraction permutation under the Riemann symmetry group (8 symmetries/factor x n! block permutations). The original brute-force O(8^n x n!) was infeasible for n>=5. This session implemented three stacked optimizations that achieve 1,000,000x speedup at n=7.

## Current Status

### Completed
- [x] `_backtrack_riemann_syms!` with frozen-position pruning (`src/XInvar.jl:1068-1155`)
- [x] Bounds-based pruning: non-frozen values use `[slot_lb, slot_ub]` from Riemann slot ranges
- [x] Block-perm deduplication: skip identical block-permuted perms (self-contracting patterns)
- [x] Block-perm lb rejection: skip dominated block perms via per-slot lower-bound check
- [x] Initial best_perm seeding from identity-symmetry block perms
- [x] Block perm lex-sorting for better pruning order
- [x] Cross-validation tests: backtracking matches brute force at n=4
- [x] Property tests: n=5 deterministic + symmetry-consistent
- [x] Performance tests: n=5 (100 calls < 5s), n=6 feasibility, n=7 (20 calls < 5s)
- [x] All 648,784 XInvar tests pass; 91 XPerm; 417+ XTensor; 709 Python

### Performance Results

| n | Brute force | Final optimized | Speedup |
|---|------------|-----------------|---------|
| 5 | ~seconds | 0.98 ms | ~1,000x |
| 6 | infeasible | 1.05 ms | ~100,000x |
| 7 | impossible | 10 ms | ~1,000,000x |
| 8 | impossible | 104 ms | new |

n=7 order-14 dispatch table (16,532 perms): ~165s total (was 75+ hours).

## Critical Files

1. `src/XInvar.jl:1068-1155` - `_backtrack_riemann_syms!`: recursive backtracking with frozen + bounded pruning
2. `src/XInvar.jl:1157-1333` - `_canonicalize_contraction_perm`: brute-force (n<=4) / backtracking (n>=5) dispatch
3. `test/julia/test_xinvar.jl:1074-1223` - Backtracking test suite (cross-validation, properties, performance)

## Key Learnings

1. **Bounds-based pruning is the critical optimization**
   - For cross-contracting perms, frozen-position pruning alone is useless (early positions map to late factors, nothing freezes)
   - But a Riemann slot of factor m can only become one of {rs_m, rs_m+1, rs_m+2, rs_m+3} — this lower bound enables pruning at position 1
   - Derivative slots are never swapped by Riemann symmetries (frozen regardless of factor order)

2. **Block-perm dedup is essential for self-contracting patterns**
   - Self-contracting perms (each factor contracts with itself) produce identical bps from all n! block perms
   - Without dedup: 5040 identical backtracking traversals for n=7
   - With dedup: 1 traversal

3. **The three optimizations are complementary**
   - Frozen pruning: handles same-factor contractions
   - Bounds pruning: handles cross-factor contractions
   - Dedup + lb rejection: handles block-perm explosion

4. **`slot_lb`/`slot_ub` arrays**
   - Precomputed per slot: Riemann slots get `[riemann_starts[factor], riemann_starts[factor]+3]`
   - Derivative slots get `[j, j]` (frozen, never changed by Riemann symmetries)
   - `src/XInvar.jl:1210-1222`

## Next Steps

1. **Phases 4 + 6: PermToInv + InvSimplify pipeline** [Priority: HIGH]
   - All orders 4-14 are now unblocked
   - Issues: sxAct-w50 (Phase 4), sxAct-23p (Phase 6)

2. **Phase 7: RiemannSimplify end-to-end** [Priority: HIGH]
   - Issue: sxAct-6i2

## Artifacts

**Modified files:**
- `src/XInvar.jl` — `_backtrack_riemann_syms!` (new), `_canonicalize_contraction_perm` (refactored)
- `test/julia/test_xinvar.jl` — Backtracking test suite

**Commits:**
- `5a71c05` — Initial backtracking with frozen-position pruning
- `7830f3b` — Bounds-based pruning + block-perm dedup + lb rejection
