---
date: 2026-03-17T10:55:45-03:00
git_commit: 0e87f68
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-tw0 (closed), sxAct-d7qy (open)
status: handoff
---

# Handoff: Invar Perm Convention Fix & End-to-End RiemannSimplify

## Context

The Wolfram Invar database stores contraction permutations in a "canonical labeling" convention (σ(i) = position of slot i in a paired arrangement), but our internal code uses contraction involutions (perm[i] = j means slot i contracts with slot j). This mismatch meant `RiemannSimplify` could never look up invariants in the real database — all prior tests passed only because synthetic DBs were built from our own perms and Phase 11 round-trips only tested DB-to-DB.

This session fixed the convention mismatch, added converters, and validated the full `RiemannSimplify` pipeline end-to-end with the real Invar database through order 8 (38 algebraic invariants). Orders 10-12 are structurally supported but blocked by O(8^n × n!) canonicalization cost — tracked as sxAct-d7qy.

Also created `docs/src/wolfram-migration.md` (Wolfram xAct migration guide) and closed epic sxAct-gc8u.

## Current Status

### Completed
- [x] `docs/src/wolfram-migration.md` — Wolfram xAct migration guide (sxAct-v07t, closed)
- [x] Epic sxAct-gc8u closed (all 13 sub-issues done)
- [x] Convention converters: `_invar_perm_to_involution`, `_involution_to_invar_perm` (`src/XInvar.jl:1408-1452`)
- [x] Lazy per-case dispatch: `_build_case_dispatch` + `_ensure_case_dispatch` (`src/XInvar.jl:1456-1523`)
- [x] `InvToPerm` returns canonical involutions for non-dual, raw perms for dual (`src/XInvar.jl:1605-1613`)
- [x] `PermToInv` uses canonical involution lookup for non-dual, raw for dual (`src/XInvar.jl:1539-1567`)
- [x] `_format_rational` emits `(N/M)` matching parser expectations (`src/XInvar.jl:1854-1860`)
- [x] End-to-end RiemannSimplify tests with real DB: known expressions + algebraic round-trip orders 2-8 (`test/julia/test_xinvar.jl:2307-2398`)
- [x] All 648,768 tests pass (sxAct-tw0, closed)
- [x] sxAct-d7qy created for order 10-12 canonicalization optimization

### Planned (sxAct-d7qy)
- [ ] Replace brute-force `_canonicalize_contraction_perm` with Schreier-Sims based approach
- [ ] Enable dispatch build for n=5 Riemanns (order 10, 204 perms)
- [ ] Enable dispatch build for n=6 Riemanns (order 12, 1613 perms)
- [ ] Add order 10-12 algebraic round-trip tests
- [ ] Consider differential case idempotency (like-term collection in InvSimplify)

## Critical Files

1. `src/XInvar.jl:1400-1530` — Convention converters, dispatch build, `_ensure_case_dispatch`
2. `src/XInvar.jl:1535-1615` — `PermToInv` and `InvToPerm` with convention handling
3. `src/XInvar.jl:1080-1159` — `_canonicalize_contraction_perm` (the O(8^n × n!) bottleneck)
4. `src/XInvar.jl:1780-1810` — `RiemannSimplify` pipeline
5. `test/julia/test_xinvar.jl:2307-2398` — End-to-end real-DB tests
6. `src/XPerm.jl` — Existing StrongGenSet/Schreier-Sims infrastructure (reusable for optimization)

## Recent Changes

- `src/XInvar.jl` — Added `_invar_perm_to_involution`, `_involution_to_invar_perm`, `_build_case_dispatch`, `_build_case_dispatch_raw`, `_ensure_case_dispatch`; modified `PermToInv`, `InvToPerm`, `_format_rational`, `_reset_invar_db!`; replaced global dispatch `Nothing` with `Dict`
- `test/julia/test_xinvar.jl` — Updated all synthetic DBs to Invar convention, updated round-trip tests, `_perm_dispatch = nothing` → `empty!(_perm_dispatch)`, added Phase 11 end-to-end tests
- `docs/src/wolfram-migration.md` — New file
- `docs/src/getting-started.md` — Cross-link to migration guide
- `docs/src/index.md` — Cross-link to migration guide
- `docs/make.jl` — Added "Migrating from Wolfram" nav entry

## Key Learnings

1. **Two permutation conventions exist and are NOT interchangeable**
   - Wolfram Invar: σ(i) = paired-position label. Pairs at (1,2), (3,4), etc. E.g., RicciScalar = `[1,3,2,4]`
   - Our internal: involution where perm[i]=j means i↔j contracted. E.g., RicciScalar = `[3,4,1,2]`
   - Conversion: `_invar_perm_to_involution` groups by `⌈σ(i)/2⌉` to find pairs
   - Verified that both canonicalization procedures agree after conversion

2. **Canonicalization is the bottleneck, not conversion**
   - `_canonicalize_contraction_perm` enumerates 8^n Riemann symmetries × n! block perms
   - n=4 (order 8): 8^4 × 4! = ~100K — fast
   - n=5 (order 10): 8^5 × 5! = ~4M — borderline (~seconds per perm × 204 = minutes)
   - n=6 (order 12): 8^6 × 6! = ~189M — infeasible (~hours for 1613 perms)
   - XPerm.jl's `canonicalize_slots()` with `StrongGenSet` can handle this in O(n²|G|) instead

3. **Dual cases need special handling**
   - Epsilon tensor adds 4 extra slots that `_canonicalize_contraction_perm` doesn't account for
   - Dual dispatch uses raw DB perms (involutions) without canonicalization
   - Dual `InvToPerm` returns raw perms; `PermToInv` looks up directly

4. **Differential invariant simplification has idempotency issues**
   - Algebraic cases (all-zero deriv_orders) round-trip perfectly
   - Differential cases ([0,2], [1,1], etc.) sometimes don't converge — the InvSimplify expansion produces terms that aren't collected into like terms
   - This is a pre-existing InvSimplify issue, not related to the convention fix

5. **`_format_rational` must emit `(N/M)` with parens**
   - The `_parse_invar_monomial` parser expects `(N/M)` format for rational coefficients
   - Without parens, re-parsing simplified expressions fails

## Open Questions

- [ ] Can `canonicalize_slots()` from XPerm.jl replace `_canonicalize_contraction_perm`? Need to express Riemann symmetry group as a `StrongGenSet` and the contraction perm as a slot configuration
- [ ] Should differential case idempotency be a separate issue from sxAct-d7qy?
- [ ] For dual cases: should we implement epsilon-aware canonicalization or keep the raw dispatch approach?

## Next Steps

1. **Optimize canonicalization (sxAct-d7qy)** [Priority: HIGH]
   - Express the Riemann pair symmetry group (S2 wr S2 per factor × block perms) as a `StrongGenSet`
   - Use `canonicalize_slots()` for O(n²|G|) canonicalization
   - This unlocks orders 10-12 dispatch and full coverage

2. **Fix differential invariant idempotency** [Priority: MEDIUM]
   - Investigate like-term collection in `InvSimplify` for CovD cases
   - May need canonical ordering of CovD indices in output expressions

3. **Add differential case round-trip tests** [Priority: LOW]
   - Once idempotency is fixed, add tests for [2], [0,2], [1,1], [4], etc.

## Artifacts

**New files:**
- `docs/src/wolfram-migration.md`

**Modified files:**
- `src/XInvar.jl`
- `test/julia/test_xinvar.jl`
- `docs/make.jl`
- `docs/src/getting-started.md`
- `docs/src/index.md`

## References

- Wolfram Invar package: http://www.xact.es/Invar/
- `plans/2026-03-11-multi-term-symmetry-engine.md` — Invar pipeline phases
- `resources/xAct/Invar/Riemann/` — 363 database files (steps 1-6)
- Beads: sxAct-tw0 (closed), sxAct-d7qy (open), sxAct-v07t (closed), sxAct-gc8u (closed)

## Test Results

- 648,768 / 648,768 XInvar Julia tests PASS (45s)
- Algebraic round-trip verified for orders 2, 4, 6, 8 (1 + 3 + 9 + 38 = 51 invariants)
- End-to-end RiemannSimplify verified for RicciScalar, Kretschner, Ricci², cubic Riemann, relabeling cancellation, curvature_relations
