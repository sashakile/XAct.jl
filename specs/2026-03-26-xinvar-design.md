# XInvar.jl — Riemann Invariant Engine Design

**Date:** 2026-03-26
**Status:** Implemented (all 11 phases)
**Location:** `src/XInvar.jl` (~2,100 lines), `src/InvarDB.jl` (~500 lines)
**Reference:** Martin-Garcia, Yllanes & Portugal (2008), arXiv:0802.1274

---

## 1. Purpose

XInvar classifies and simplifies Riemann polynomial invariants. It is a database-driven
port of the Wolfram `Invar.m` package — it uses pre-computed identity tables rather than
algorithmic re-derivation.

## 2. Core Types

```julia
struct InvariantCase
    deriv_orders::Vector{Int}   # sorted; length = degree of Riemann polynomial
    n_epsilon::Int              # 0 = non-dual, 1 = dual (4D Levi-Civita)
end

struct RPerm                    # Riemann in permutation representation
    metric::Symbol
    case::InvariantCase
    perm::Vector{Int}           # contraction pattern (images notation)
end

struct RInv                     # Riemann with canonical database index
    metric::Symbol
    case::InvariantCase
    index::Int                  # 1-based index from Invar database
end
```

## 3. The 11 Phases

| Phase | Feature | Description |
|-------|---------|-------------|
| 1 | InvariantCase enumeration | `InvarCases()` / `InvarDualCases()` |
| 2 | RPerm/RInv types | Permutation representation primitives |
| 3 | RiemannToPerm | Convert Riemann products to permutation form |
| 4 | PermToInv | Database lookup: permutation → canonical index |
| 5 | Database loading | InvarDB.jl parses Maple + Mathematica formats |
| 6 | InvSimplify | 6-level simplification pipeline |
| 7 | RiemannSimplify | End-to-end user-facing simplification |
| 8 | Generalized CovD commutation | SortCovDs with Riemann corrections |
| 9 | Dimension-dependent identities | Identities valid only in specific dimensions |
| 10 | Dual invariants | Levi-Civita tensor and dual (epsilon) invariants |
| 11 | Validation benchmarks | 648,825 tests against known results |

## 4. InvSimplify Pipeline

Six levels applied in sequence:

1. **Cyclic symmetry** — R_{abcd} = R_{cdab}
2. **Bianchi** — first Bianchi identity
3. **CovD commutation** — canonical ordering of covariant derivative chains
4. **Dimension-dependent** — identities that hold only in dim ≤ D
5. **Dual** — epsilon tensor relations (4D only)
6. **Database reduction** — express in terms of independent invariants via InvarDB

## 5. Database (InvarDB.jl)

- Parses both **Maple** and **Mathematica** export formats from the original Invar project.
- 48 non-dual cases + 15 dual cases through order 10-14.
- `MaxIndex` (50 entries) and `MaxDualIndex` (17 entries) bound the canonical index ranges.
- Rules stored as rational-coefficient linear combinations of canonical invariants.

## 6. Test Coverage

648,825 Julia tests pass, exhaustively verifying all case/index combinations against
the Wolfram reference implementation.
