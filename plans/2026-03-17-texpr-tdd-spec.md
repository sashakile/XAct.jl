# TExpr Stage 1 — TDD Implementation Spec

**Parent:** `plans/2026-03-17-typed-expression-api.md`
**Date:** 2026-03-17

## Overview

Test-driven implementation of the typed expression layer (Stage 1).
All tests are written **before** the implementation. The cycle is:

1. Write a batch of red tests for one component
2. Implement just enough to make them green
3. Refactor if needed
4. Move to the next component

## File Layout

```
src/TExpr.jl                           # New Julia module
test/julia/test_texpr.jl               # Julia tests
packages/xact-py/src/xact/expr.py      # New Python module
tests/unit/test_texpr.py               # Python tests
```

`src/TExpr.jl` is `include()`d from `src/xAct.jl` after `XTensor.jl`.
Exports: `Idx`, `DnIdx`, `TensorHead`, `CovDHead`, `TExpr`, `TTensor`,
`TProd`, `TSum`, `TScalar`, `TCovD`, `@indices`, `tensor`, `covd`.

## TDD Batches

Each batch lists the tests to write first (RED), then the implementation
target (GREEN). Tests are ordered by dependency: later batches build on
earlier ones.

---

### Batch 1: Index Types

**File:** `test/julia/test_texpr.jl`

```julia
@testset "TExpr" begin

@testset "Idx — construction and validation" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

    # Valid construction
    i = Idx(:tea, :TE4)
    @test i.label == :tea
    @test i.manifold == :TE4

    # Invalid manifold
    @test_throws ErrorException Idx(:tea, :NoSuchManifold)

    # Invalid label for manifold
    @test_throws ErrorException Idx(:zzz, :TE4)
end

@testset "DnIdx — covariant index via negation" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

    i = Idx(:tea, :TE4)
    di = -i
    @test di isa DnIdx
    @test di.parent === i
    @test di.parent.label == :tea

    # Double negation returns bare Idx
    @test -di === i
    @test (-di) isa Idx
end

@testset "@indices macro" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

    @indices TE4 tea teb tec ted
    @test tea isa Idx
    @test tea.label == :tea
    @test tea.manifold == :TE4
    @test teb.label == :teb

    # Negation works on macro-created indices
    @test (-tea) isa DnIdx
    @test (-tea).parent.label == :tea
end
```

**Implement:** `Idx` struct with inner constructor validation, `DnIdx`
struct, `Base.:-(::Idx)`, `Base.:-(::DnIdx)`, `@indices` macro.

---

### Batch 2: TensorHead & tensor()

```julia
@testset "TensorHead & tensor() lookup" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TEV, ["tea"], :TE4)

    # Lookup registered tensor
    th = tensor(:TEV)
    @test th isa TensorHead
    @test th.name == :TEV

    # String convenience
    @test tensor("TEV").name == :TEV

    # Unregistered tensor throws
    @test_throws ErrorException tensor(:NoSuchTensor)
end

@testset "tensor() after reset_state!" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TEW, ["tea"], :TE4)
    th = tensor(:TEW)
    @test th.name == :TEW

    reset_state!()

    # Handle is stale — tensor() should error
    @test_throws ErrorException tensor(:TEW)
end

@testset "tensor() for auto-created tensors" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)

    # All auto-created tensors are accessible
    @test tensor(:TEg) isa TensorHead
    @test tensor(:RiemannTECD) isa TensorHead
    @test tensor(:RicciTECD) isa TensorHead
    @test tensor(:RicciScalarTECD) isa TensorHead
    @test tensor(:EinsteinTECD) isa TensorHead
    @test tensor(:WeylTECD) isa TensorHead
end
```

**Implement:** `TensorHead` struct, `tensor(::Symbol)`, `tensor(::String)`.

---

### Batch 3: TTensor via getindex

```julia
@testset "TTensor — getindex on TensorHead" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")
    def_tensor!(:TEV, ["tea"], :TE4)
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)

    @indices TE4 tea teb tec ted

    T = tensor(:TET)
    V = tensor(:TEV)

    # Basic application
    t1 = T[-tea, -teb]
    @test t1 isa TTensor
    @test t1.head.name == :TET
    @test length(t1.indices) == 2
    @test t1.indices[1] isa DnIdx
    @test t1.indices[2] isa DnIdx

    # Contravariant
    v1 = V[tea]
    @test v1 isa TTensor
    @test v1.indices[1] isa Idx

    # Rank-0 (scalar)
    RS = tensor(:RicciScalarTECD)
    rs = RS[]
    @test rs isa TTensor
    @test isempty(rs.indices)
end

@testset "TTensor — slot count validation" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb tec ted
    T = tensor(:TET)

    # Too many indices
    @test_throws ErrorException T[-tea, -teb, -tec]

    # Too few indices
    @test_throws ErrorException T[-tea]
end

@testset "TTensor — manifold validation" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_manifold!(:TE3, 3, [:t3a, :t3b, :t3c])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb
    @indices TE3 t3a t3b
    T = tensor(:TET)

    # Indices from wrong manifold
    @test_throws ErrorException T[-t3a, -t3b]

    # Mixed manifolds
    @test_throws ErrorException T[-tea, -t3b]
end

@testset "TTensor — stale head after reset" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb
    T = tensor(:TET)

    reset_state!()

    # Head is stale — getindex should error with helpful message
    @test_throws ErrorException T[-tea, -teb]
end
```

**Implement:** `Base.getindex(::TensorHead, ::SlotIdx...)`,
`Base.getindex(::TensorHead)`, `_validate_tensor_indices()`.

---

### Batch 4: Arithmetic Operators

```julia
@testset "TProd — multiplication" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TEV, ["tea"], :TE4)

    @indices TE4 tea teb tec ted
    T = tensor(:TET)
    V = tensor(:TEV)

    # TExpr * TExpr
    p = T[-tea, -teb] * V[tea]
    @test p isa TProd
    @test p.coeff == 1//1
    @test length(p.factors) == 2

    # Integer * TExpr
    p2 = 2 * T[-tea, -teb]
    @test p2 isa TProd
    @test p2.coeff == 2//1
    @test length(p2.factors) == 1

    # TExpr * Integer
    p3 = T[-tea, -teb] * 3
    @test p3 isa TProd
    @test p3.coeff == 3//1

    # Rational * TExpr
    p4 = (1//2) * T[-tea, -teb]
    @test p4 isa TProd
    @test p4.coeff == 1//2

    # Negation
    p5 = -T[-tea, -teb]
    @test p5 isa TProd
    @test p5.coeff == -1//1
end

@testset "TProd — flattening" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TEV, ["tea"], :TE4)
    def_tensor!(:TEW, ["tea"], :TE4)

    @indices TE4 tea teb tec ted
    T = tensor(:TET)
    V = tensor(:TEV)
    W = tensor(:TEW)

    # (T * V) * W should be flat (3 factors), not nested
    p = (T[-tea, -teb] * V[tea]) * W[tec]
    @test p isa TProd
    @test length(p.factors) == 3

    # Coefficient merging: 2 * (3 * T) = 6 * T
    p2 = 2 * (3 * T[-tea, -teb])
    @test p2 isa TProd
    @test p2.coeff == 6//1
    @test length(p2.factors) == 1
end

@testset "TSum — addition and subtraction" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TES, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb tec ted
    T = tensor(:TET)
    S = tensor(:TES)

    # TExpr + TExpr
    s = T[-tea, -teb] + S[-tea, -teb]
    @test s isa TSum
    @test length(s.terms) == 2

    # TExpr - TExpr
    d = T[-tea, -teb] - S[-tea, -teb]
    @test d isa TSum
    @test length(d.terms) == 2
    # Second term should be negated
    @test d.terms[2] isa TProd
    @test d.terms[2].coeff == -1//1
end

@testset "TSum — flattening" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TES, ["-tea", "-teb"], :TE4)
    def_tensor!(:TEU, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb tec ted
    T = tensor(:TET)
    S = tensor(:TES)
    U = tensor(:TEU)

    # (T + S) + U should be flat (3 terms), not nested
    s = (T[-tea, -teb] + S[-tea, -teb]) + U[-tea, -teb]
    @test s isa TSum
    @test length(s.terms) == 3
end

@testset "TScalar" begin
    s = TScalar(3//2)
    @test s isa TExpr
    @test s.value == 3//2
end
```

**Implement:** All `Base.:+`, `Base.:-`, `Base.:*` overloads, `_flatten_prod`,
`_flatten_sum`, `_make_prod`. `TScalar`.

---

### Batch 5: CovDHead & TCovD

```julia
@testset "CovDHead & covd() lookup" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)

    cd = covd(:TECD)
    @test cd isa CovDHead
    @test cd.name == :TECD

    # String convenience
    @test covd("TECD").name == :TECD

    # Unregistered CovD
    @test_throws ErrorException covd(:NoSuchCD)
end

@testset "TCovD — covariant derivative expressions" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)
    def_tensor!(:TEphi, String[], :TE4)

    @indices TE4 tea teb tec ted
    CD = covd(:TECD)
    phi = tensor(:TEphi)

    # Single derivative: CD[-tea](phi[])
    e1 = CD[-tea](phi[])
    @test e1 isa TCovD
    @test e1.covd == :TECD
    @test e1.index isa DnIdx
    @test e1.index.parent.label == :tea
    @test e1.operand isa TTensor

    # Nested: CD[-tea](CD[-teb](phi[]))
    e2 = CD[-tea](CD[-teb](phi[]))
    @test e2 isa TCovD
    @test e2.operand isa TCovD
    @test e2.operand.index.parent.label == :teb
end

@testset "TCovD — derivative of tensor" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb tec ted
    CD = covd(:TECD)
    T = tensor(:TET)

    # CD[-tec](T[-tea, -teb])
    e = CD[-tec](T[-tea, -teb])
    @test e isa TCovD
    @test e.operand isa TTensor
    @test e.operand.head.name == :TET
end
```

**Implement:** `CovDHead`, `covd()`, `_CovDApplicator`,
`Base.getindex(::CovDHead, ::SlotIdx)`, `(::_CovDApplicator)(::TExpr)`.

---

### Batch 6: String Serialization

```julia
@testset "_to_string — indices" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

    @indices TE4 tea teb

    @test _to_string(tea) == "tea"
    @test _to_string(-tea) == "-tea"
end

@testset "_to_string — TTensor" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)

    @indices TE4 tea teb
    T = tensor(:TET)
    RS = tensor(:RicciScalarTECD)

    @test _to_string(T[-tea, -teb]) == "TET[-tea,-teb]"

    # Contravariant indices
    def_tensor!(:TEV, ["tea"], :TE4)
    V = tensor(:TEV)
    @test _to_string(V[tea]) == "TEV[tea]"

    # Rank-0
    @test _to_string(RS[]) == "RicciScalarTECD[]"
end

@testset "_to_string — TScalar" begin
    @test _to_string(TScalar(3//1)) == "3"
    @test _to_string(TScalar(-1//1)) == "-1"
    @test _to_string(TScalar(3//2)) == "(3/2)"
    @test _to_string(TScalar(-1//2)) == "(-1/2)"
end

@testset "_to_string — TProd" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TEV, ["tea"], :TE4)

    @indices TE4 tea teb
    T = tensor(:TET)
    V = tensor(:TEV)

    # coeff = 1
    @test _to_string(T[-tea, -teb] * V[tea]) == "TET[-tea,-teb] * TEV[tea]"

    # coeff = -1
    @test _to_string(-(T[-tea, -teb])) == "-TET[-tea,-teb]"

    # coeff = 2
    @test _to_string(2 * T[-tea, -teb]) == "2 * TET[-tea,-teb]"

    # coeff = 1//2
    @test _to_string((1//2) * T[-tea, -teb]) == "(1/2) * TET[-tea,-teb]"
end

@testset "_to_string — TProd with parenthesized sub-sums" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TES, ["-tea", "-teb"], :TE4)
    def_tensor!(:TEV, ["tea"], :TE4)

    @indices TE4 tea teb
    T = tensor(:TET)
    S = tensor(:TES)
    V = tensor(:TEV)

    # (T + S) * V should parenthesize the sum
    str = _to_string((T[-tea, -teb] + S[-tea, -teb]) * V[tea])
    @test startswith(str, "(")
    @test occursin("TET[-tea,-teb]", str)
    @test occursin("TES[-tea,-teb]", str)
    @test occursin("TEV[tea]", str)
end

@testset "_to_string — TSum" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)
    def_tensor!(:TES, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb
    T = tensor(:TET)
    S = tensor(:TES)

    # Addition: T + S
    @test _to_string(T[-tea, -teb] + S[-tea, -teb]) ==
        "TET[-tea,-teb] + TES[-tea,-teb]"

    # Subtraction: T - S  should produce " - " not " + -"
    str = _to_string(T[-tea, -teb] - S[-tea, -teb])
    @test !occursin("+ -", str)
    @test occursin(" - ", str)
end

@testset "_to_string — TCovD" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)
    def_tensor!(:TEphi, String[], :TE4)
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb tec
    CD = covd(:TECD)
    phi = tensor(:TEphi)
    T = tensor(:TET)

    # Single CovD
    @test _to_string(CD[-tea](phi[])) == "TECD[-tea][TEphi[]]"

    # Nested CovD
    @test _to_string(CD[-tea](CD[-teb](phi[]))) ==
        "TECD[-tea][TECD[-teb][TEphi[]]]"

    # CovD of tensor
    @test _to_string(CD[-tec](T[-tea, -teb])) ==
        "TECD[-tec][TET[-tea,-teb]]"
end
```

**Implement:** All `_to_string()` methods, `_to_string_factor()`.

---

### Batch 7: show() Display

```julia
@testset "show() — REPL display matches _to_string" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4)

    @indices TE4 tea teb
    T = tensor(:TET)

    buf = IOBuffer()

    # TTensor
    show(buf, T[-tea, -teb])
    @test String(take!(buf)) == "TET[-tea,-teb]"

    # TSum
    show(buf, T[-tea, -teb] + T[-teb, -tea])
    @test String(take!(buf)) == "TET[-tea,-teb] + TET[-teb,-tea]"

    # TensorHead shows type info, not expression
    show(buf, T)
    @test occursin("TensorHead", String(take!(buf)))

    # Idx
    show(buf, tea)
    @test String(take!(buf)) == "tea"

    # DnIdx
    show(buf, -tea)
    @test String(take!(buf)) == "-tea"
end
```

**Implement:** `Base.show(::IO, ::TExpr)`, `Base.show(::IO, ::Idx)`,
`Base.show(::IO, ::DnIdx)`, `Base.show(::IO, ::TensorHead)`.

---

### Batch 8: Engine Integration (Round-Trip)

This is the critical batch — typed expressions must produce the same
results as string expressions when passed through the engine.

```julia
@testset "ToCanonical — typed vs string equivalence" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)
    def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")

    @indices TE4 tea teb tec ted

    T = tensor(:TET)
    Riem = tensor(:RiemannTECD)
    g = tensor(:TEg)

    # Symmetric tensor: T[-b,-a] - T[-a,-b] = 0
    @test ToCanonical(T[-teb, -tea] - T[-tea, -teb]) == "0"
    @test ToCanonical(T[-teb, -tea] - T[-tea, -teb]) ==
        ToCanonical("TET[-teb,-tea] - TET[-tea,-teb]")

    # First Bianchi identity
    bianchi = Riem[-tea,-teb,-tec,-ted] +
              Riem[-tea,-tec,-ted,-teb] +
              Riem[-tea,-ted,-teb,-tec]
    @test ToCanonical(bianchi) == "0"

    # Pair symmetry
    @test ToCanonical(Riem[-tea,-teb,-tec,-ted] - Riem[-tec,-ted,-tea,-teb]) == "0"

    # Antisymmetry
    @test ToCanonical(Riem[-tea,-teb,-tec,-ted] + Riem[-teb,-tea,-tec,-ted]) == "0"
end

@testset "Contract — typed vs string equivalence" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)
    def_tensor!(:TEV, ["tea"], :TE4)

    @indices TE4 tea teb tec ted
    V = tensor(:TEV)
    g = tensor(:TEg)

    # V[a] * g[-a,-b] should contract
    typed_result = Contract(V[tea] * g[-tea, -teb])
    string_result = Contract("TEV[tea] * TEg[-tea,-teb]")
    @test typed_result == string_result
end

@testset "Simplify — typed vs string equivalence" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)

    @indices TE4 tea teb
    g = tensor(:TEg)

    typed_result = Simplify(g[-tea, -teb])
    string_result = Simplify("TEg[-tea,-teb]")
    @test typed_result == string_result
end

@testset "perturb — typed vs string equivalence" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_metric!(-1, "TEg[-tea,-teb]", :TECD)
    def_tensor!(:TEh, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")
    def_perturbation!(:TEh, :TEg, 1)

    @indices TE4 tea teb
    g = tensor(:TEg)

    typed_result = perturb(g[-tea, -teb], 1)
    string_result = perturb("TEg[-tea,-teb]", 1)
    @test typed_result == string_result
end
```

**Implement:** `TExpr` method overloads for `ToCanonical`, `Contract`,
`Simplify`, `perturb`, `CommuteCovDs`, `SortCovDs`, `IBP`,
`TotalDerivativeQ`, `VarD`.

---

### Batch 9: Coefficient Edge Cases

```julia
@testset "Coefficient edge cases" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")

    @indices TE4 tea teb
    T = tensor(:TET)

    # 0 * T should produce a zero-coefficient product
    z = 0 * T[-tea, -teb]
    @test z isa TProd
    @test z.coeff == 0//1

    # 1 * T should not nest
    o = 1 * T[-tea, -teb]
    @test o isa TProd
    @test o.coeff == 1//1
    @test length(o.factors) == 1

    # Negative rational
    n = (-3//7) * T[-tea, -teb]
    @test n.coeff == -3//7

    # Three-way product with coefficients: 2 * (3 * T) * 5
    # Should merge: coeff = 30
    p = (2 * (3 * T[-tea, -teb])) * 5
    @test p isa TProd
    @test p.coeff == 30//1
end

@testset "Multi-term expression string round-trip" begin
    reset_state!()
    def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
    def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")
    def_tensor!(:TES, ["-tea", "-teb"], :TE4)
    def_tensor!(:TEV, ["tea"], :TE4)

    @indices TE4 tea teb tec ted
    T = tensor(:TET)
    S = tensor(:TES)
    V = tensor(:TEV)

    # Complex expression: 2*T[-a,-b] - (3//2)*S[-a,-b] + T[-b,-a]
    expr = 2 * T[-tea, -teb] - (3//2) * S[-tea, -teb] + T[-teb, -tea]
    str = _to_string(expr)

    # Should parse correctly by the engine
    result = ToCanonical(expr)
    @test result isa String
    # 2*T + T = 3*T (symmetric), so T[-tea,-teb] terms merge
    # Can't predict exact form, but it shouldn't error
end
```

**Implement:** No new code — these validate earlier batches work correctly
together.

---

### Python Tests

**File:** `tests/unit/test_texpr.py`

```python
"""Unit tests for typed expression API (xact.expr)."""

import pytest

import xact
from xact.expr import Idx, DnIdx, TensorHead, AppliedTensor


@pytest.fixture(autouse=True)
def _reset():
    xact.reset()


@pytest.fixture()
def manifold():
    return xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])


@pytest.fixture()
def metric(manifold):
    return xact.Metric(manifold, "g", signature=-1, covd="CD")


class TestIdx:
    def test_create(self, manifold):
        a, b, c, d, e, f = xact.indices(manifold)
        assert a.label == "a"
        assert a.manifold == "M"

    def test_neg_creates_dnidx(self, manifold):
        a, *_ = xact.indices(manifold)
        da = -a
        assert isinstance(da, DnIdx)
        assert da.parent is a

    def test_double_neg(self, manifold):
        a, *_ = xact.indices(manifold)
        assert -(-a) is a

    def test_repr(self, manifold):
        a, *_ = xact.indices(manifold)
        assert repr(a) == "a"
        assert repr(-a) == "-a"

    def test_indices_count(self, manifold):
        indices = xact.indices(manifold)
        assert len(indices) == 6


class TestTensorHead:
    def test_lookup(self, manifold, metric):
        th = xact.tensor("g")
        assert isinstance(th, TensorHead)
        assert th.name == "g"

    def test_auto_tensors(self, manifold, metric):
        assert xact.tensor("RiemannCD").name == "RiemannCD"
        assert xact.tensor("RicciCD").name == "RicciCD"

    def test_unregistered(self, manifold, metric):
        with pytest.raises(ValueError):
            xact.tensor("NoSuchTensor")

    def test_repr(self, manifold, metric):
        th = xact.tensor("g")
        assert "TensorHead" in repr(th)


class TestAppliedTensor:
    def test_getitem(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        t = g[-a, -b]
        assert isinstance(t, AppliedTensor)
        assert len(t.indices) == 2

    def test_slot_count_error(self, manifold, metric):
        a, b, c, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        with pytest.raises((ValueError, IndexError)):
            g[-a, -b, -c]

    def test_str(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        assert str(g[-a, -b]) == "g[-a,-b]"

    def test_tensor_class_getitem(self, manifold, metric):
        """Tensor definition objects also support __getitem__."""
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold, symmetry="Symmetric[{-a,-b}]")
        t = T[-a, -b]
        assert isinstance(t, AppliedTensor)
        assert str(t) == "T[-a,-b]"

    def test_metric_class_getitem(self, manifold, metric):
        """Metric definition objects also support __getitem__."""
        a, b, *_ = xact.indices(manifold)
        t = metric[-a, -b]
        assert isinstance(t, AppliedTensor)
        assert str(t) == "g[-a,-b]"


class TestArithmetic:
    def test_add(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        S = xact.Tensor("S", ["-a", "-b"], manifold)
        expr = T[-a, -b] + S[-a, -b]
        assert "T[-a,-b]" in str(expr)
        assert "S[-a,-b]" in str(expr)
        assert "+" in str(expr)

    def test_sub(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        S = xact.Tensor("S", ["-a", "-b"], manifold)
        expr = T[-a, -b] - S[-a, -b]
        s = str(expr)
        assert " - " in s
        assert "+ -" not in s

    def test_scalar_mul(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        expr = 2 * T[-a, -b]
        assert str(expr).startswith("2")

    def test_neg(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        expr = -T[-a, -b]
        assert str(expr).startswith("-")

    def test_tensor_product(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        V = xact.Tensor("V", ["a"], manifold)
        expr = T[-a, -b] * V[a]
        assert "T[-a,-b]" in str(expr)
        assert "V[a]" in str(expr)


class TestEngineIntegration:
    def test_canonicalize_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold, symmetry="Symmetric[{-a,-b}]")
        result = xact.canonicalize(T[-b, -a] - T[-a, -b])
        assert result == "0"

    def test_canonicalize_typed_matches_string(self, manifold, metric):
        a, b, c, d, *_ = xact.indices(manifold)
        Riem = xact.tensor("RiemannCD")
        typed = xact.canonicalize(
            Riem[-a, -b, -c, -d] + Riem[-a, -c, -d, -b] + Riem[-a, -d, -b, -c]
        )
        string = xact.canonicalize(
            "RiemannCD[-a,-b,-c,-d] + RiemannCD[-a,-c,-d,-b] + RiemannCD[-a,-d,-b,-c]"
        )
        assert typed == string == "0"

    def test_contract_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        V = xact.Tensor("V", ["a"], manifold)
        g = xact.tensor("g")
        typed = xact.contract(V[a] * g[-a, -b])
        string = xact.contract("V[a] * g[-a,-b]")
        assert typed == string

    def test_simplify_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        typed = xact.simplify(g[-a, -b])
        string = xact.simplify("g[-a,-b]")
        assert typed == string

    def test_perturb_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        h = xact.Tensor("h", ["-a", "-b"], manifold, symmetry="Symmetric[{-a,-b}]")
        xact.Perturbation(h, metric, order=1)
        g = xact.tensor("g")
        typed = xact.perturb(g[-a, -b], order=1)
        string = xact.perturb("g[-a,-b]", order=1)
        assert typed == string
```

---

## Implementation Order

| Step | Batch | Tests (Julia) | Tests (Python) | Code |
|------|-------|---------------|----------------|------|
| 1 | Index types | 3 testsets | TestIdx (5) | Idx, DnIdx, @indices |
| 2 | TensorHead | 3 testsets | TestTensorHead (4) | TensorHead, tensor() |
| 3 | TTensor | 4 testsets | TestAppliedTensor (5) | getindex, validation |
| 4 | Arithmetic | 4 testsets | TestArithmetic (5) | +, -, *, flatten |
| 5 | CovD | 3 testsets | — | CovDHead, covd() |
| 6 | Serialization | 6 testsets | (covered by str()) | _to_string |
| 7 | Display | 1 testset | (covered by repr()) | show() |
| 8 | Engine integration | 4 testsets | TestEngineIntegration (5) | TExpr overloads |
| 9 | Edge cases | 2 testsets | — | (validates earlier) |

**Estimated totals:**
- Julia: ~30 testsets, ~120 assertions
- Python: ~6 test classes, ~30 tests
- Implementation: ~350 lines Julia, ~200 lines Python

## Running Tests

```bash
# Julia tests only (fast iteration)
julia --project=. test/julia/test_texpr.jl

# Python tests only
uv run pytest tests/unit/test_texpr.py -v

# Full suite (verify no regressions)
julia --project=. test/runtests.jl
uv run pytest tests/ -q --ignore=tests/integration --ignore=tests/properties --ignore=tests/xperm --ignore=tests/xtensor
```
