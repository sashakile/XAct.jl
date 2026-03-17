"""
Tests for TExpr typed expression layer (batches 1-9).
Run: julia --project=. test/julia/test_texpr.jl
"""

using Test

# Bootstrap — load via xAct (same as all other test files)
include(joinpath(@__DIR__, "../../src/xAct.jl"))
using .xAct

@testset "TExpr" begin

    # ---------------------------------------------------------------------------
    # Batch 1: Index Types
    # ---------------------------------------------------------------------------

    @testset "Idx — construction and validation" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

        i = Idx(:tea, :TE4)
        @test i.label == :tea
        @test i.manifold == :TE4

        @test_throws ErrorException Idx(:tea, :NoSuchManifold)
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

        @test (-tea) isa DnIdx
        @test (-tea).parent.label == :tea
    end

    # ---------------------------------------------------------------------------
    # Batch 2: TensorHead & tensor()
    # ---------------------------------------------------------------------------

    @testset "TensorHead & tensor() lookup" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TEV, ["tea"], :TE4)

        th = tensor(:TEV)
        @test th isa TensorHead
        @test th.name == :TEV

        @test tensor("TEV").name == :TEV

        @test_throws ErrorException tensor(:NoSuchTensor)
    end

    @testset "tensor() after reset_state!" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TEW, ["tea"], :TE4)
        th = tensor(:TEW)
        @test th.name == :TEW

        reset_state!()

        @test_throws ErrorException tensor(:TEW)
    end

    @testset "tensor() for auto-created tensors" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)

        @test tensor(:TEg) isa TensorHead
        @test tensor(:RiemannTECD) isa TensorHead
        @test tensor(:RicciTECD) isa TensorHead
        @test tensor(:RicciScalarTECD) isa TensorHead
        @test tensor(:EinsteinTECD) isa TensorHead
        @test tensor(:WeylTECD) isa TensorHead
    end

    # ---------------------------------------------------------------------------
    # Batch 3: TTensor via getindex
    # ---------------------------------------------------------------------------

    @testset "TTensor — getindex on TensorHead" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")
        def_tensor!(:TEV, ["tea"], :TE4)
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)

        @indices TE4 tea teb tec ted

        T = tensor(:TET)
        V = tensor(:TEV)

        t1 = T[-tea, -teb]
        @test t1 isa TTensor
        @test t1.head.name == :TET
        @test length(t1.indices) == 2
        @test t1.indices[1] isa DnIdx
        @test t1.indices[2] isa DnIdx

        v1 = V[tea]
        @test v1 isa TTensor
        @test v1.indices[1] isa Idx

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

        @test_throws ErrorException T[-tea, -teb, -tec]
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

        @test_throws ErrorException T[-t3a, -t3b]
        @test_throws ErrorException T[-tea, -t3b]
    end

    @testset "TTensor — stale head after reset" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)

        @indices TE4 tea teb
        T = tensor(:TET)

        reset_state!()

        @test_throws ErrorException T[-tea, -teb]
    end

    # ---------------------------------------------------------------------------
    # Batch 4: Arithmetic Operators
    # ---------------------------------------------------------------------------

    @testset "TProd — multiplication" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)
        def_tensor!(:TEV, ["tea"], :TE4)

        @indices TE4 tea teb tec ted
        T = tensor(:TET)
        V = tensor(:TEV)

        p = T[-tea, -teb] * V[tea]
        @test p isa TProd
        @test p.coeff == 1//1
        @test length(p.factors) == 2

        p2 = 2 * T[-tea, -teb]
        @test p2 isa TProd
        @test p2.coeff == 2//1
        @test length(p2.factors) == 1

        p3 = T[-tea, -teb] * 3
        @test p3 isa TProd
        @test p3.coeff == 3//1

        p4 = (1//2) * T[-tea, -teb]
        @test p4 isa TProd
        @test p4.coeff == 1//2

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

        p = (T[-tea, -teb] * V[tea]) * W[tec]
        @test p isa TProd
        @test length(p.factors) == 3

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

        s = T[-tea, -teb] + S[-tea, -teb]
        @test s isa TSum
        @test length(s.terms) == 2

        d = T[-tea, -teb] - S[-tea, -teb]
        @test d isa TSum
        @test length(d.terms) == 2
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

        s = (T[-tea, -teb] + S[-tea, -teb]) + U[-tea, -teb]
        @test s isa TSum
        @test length(s.terms) == 3
    end

    @testset "TScalar" begin
        s = TScalar(3//2)
        @test s isa TExpr
        @test s.value == 3//2
    end

    # ---------------------------------------------------------------------------
    # Batch 5: CovDHead & TCovD
    # ---------------------------------------------------------------------------

    @testset "CovDHead & covd() lookup" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)

        cd = covd(:TECD)
        @test cd isa CovDHead
        @test cd.name == :TECD

        @test covd("TECD").name == :TECD

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

        e1 = CD[-tea](phi[])
        @test e1 isa TCovD
        @test e1.covd == :TECD
        @test e1.index isa DnIdx
        @test e1.index.parent.label == :tea
        @test e1.operand isa TTensor

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

        e = CD[-tec](T[-tea, -teb])
        @test e isa TCovD
        @test e.operand isa TTensor
        @test e.operand.head.name == :TET
    end

    # ---------------------------------------------------------------------------
    # Batch 6: String Serialization
    # ---------------------------------------------------------------------------

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

        def_tensor!(:TEV, ["tea"], :TE4)
        V = tensor(:TEV)
        @test _to_string(V[tea]) == "TEV[tea]"

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

        @test _to_string(T[-tea, -teb] * V[tea]) == "TET[-tea,-teb] TEV[tea]"
        @test _to_string(-(T[-tea, -teb])) == "-TET[-tea,-teb]"
        @test _to_string(2 * T[-tea, -teb]) == "2 TET[-tea,-teb]"
        @test _to_string((1//2) * T[-tea, -teb]) == "(1/2) TET[-tea,-teb]"
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

        @test _to_string(T[-tea, -teb] + S[-tea, -teb]) == "TET[-tea,-teb] + TES[-tea,-teb]"

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

        @test _to_string(CD[-tea](phi[])) == "TECD[-tea][TEphi[]]"
        @test _to_string(CD[-tea](CD[-teb](phi[]))) == "TECD[-tea][TECD[-teb][TEphi[]]]"
        @test _to_string(CD[-tec](T[-tea, -teb])) == "TECD[-tec][TET[-tea,-teb]]"
    end

    # ---------------------------------------------------------------------------
    # Batch 7: show() Display
    # ---------------------------------------------------------------------------

    @testset "show() — REPL display matches _to_string" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)

        @indices TE4 tea teb
        T = tensor(:TET)

        buf = IOBuffer()

        show(buf, T[-tea, -teb])
        @test String(take!(buf)) == "TET[-tea,-teb]"

        show(buf, T[-tea, -teb] + T[-teb, -tea])
        @test String(take!(buf)) == "TET[-tea,-teb] + TET[-teb,-tea]"

        show(buf, T)
        @test occursin("TensorHead", String(take!(buf)))

        show(buf, tea)
        @test String(take!(buf)) == "tea"

        show(buf, -tea)
        @test String(take!(buf)) == "-tea"
    end

    # ---------------------------------------------------------------------------
    # Batch 8: Engine Integration (Round-Trip)
    # ---------------------------------------------------------------------------

    @testset "ToCanonical — typed vs string equivalence" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")

        @indices TE4 tea teb tec ted

        T = tensor(:TET)
        Riem = tensor(:RiemannTECD)
        g = tensor(:TEg)

        @test ToCanonical(T[-teb, -tea] - T[-tea, -teb]) == "0"
        @test ToCanonical(T[-teb, -tea] - T[-tea, -teb]) ==
            ToCanonical("TET[-teb,-tea] - TET[-tea,-teb]")

        bianchi =
            Riem[-tea, -teb, -tec, -ted] +
            Riem[-tea, -tec, -ted, -teb] +
            Riem[-tea, -ted, -teb, -tec]
        @test ToCanonical(bianchi) == "0"

        @test ToCanonical(Riem[-tea, -teb, -tec, -ted] - Riem[-tec, -ted, -tea, -teb]) ==
            "0"
        @test ToCanonical(Riem[-tea, -teb, -tec, -ted] + Riem[-teb, -tea, -tec, -ted]) ==
            "0"
    end

    @testset "Contract — typed vs string equivalence" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TEV, ["tea"], :TE4)

        @indices TE4 tea teb tec ted
        V = tensor(:TEV)
        g = tensor(:TEg)

        typed_result = Contract(V[tea] * g[-tea, -teb])
        # Compare against space-format string (same format _to_string now produces)
        string_result = Contract("TEV[tea] TEg[-tea,-teb]")
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

    @testset "perturb — typed result is TExpr matching string result" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TEh, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")
        def_perturbation!(:TEh, :TEg, 1)

        @indices TE4 tea teb
        g = tensor(:TEg)

        typed_result = perturb(g[-tea, -teb], 1)
        string_result = perturb("TEg[-tea,-teb]", 1)
        @test typed_result isa TExpr
        @test typed_result == string_result  # TExpr == String via _to_string
    end

    # ---------------------------------------------------------------------------
    # Batch 9: Coefficient Edge Cases
    # ---------------------------------------------------------------------------

    @testset "Coefficient edge cases" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")

        @indices TE4 tea teb
        T = tensor(:TET)

        z = 0 * T[-tea, -teb]
        @test z isa TProd
        @test z.coeff == 0//1

        o = 1 * T[-tea, -teb]
        @test o isa TProd
        @test o.coeff == 1//1
        @test length(o.factors) == 1

        n = (-3//7) * T[-tea, -teb]
        @test n.coeff == -3//7

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

        expr = 2 * T[-tea, -teb] - (3//2) * S[-tea, -teb] + T[-teb, -tea]
        result = ToCanonical(expr)
        @test result isa TExpr
    end
    # ---------------------------------------------------------------------------
    # Batch 10: Parser (_parse_to_texpr) and Round-Trip
    # ---------------------------------------------------------------------------

    @testset "_parse_to_texpr — zero" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

        r = _parse_to_texpr("0")
        @test r isa TScalar
        @test r.value == 0//1
    end

    @testset "_parse_to_texpr — single tensor" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)

        r = _parse_to_texpr("TET[-tea,-teb]")
        @test r isa TTensor
        @test r.head.name == :TET
        @test length(r.indices) == 2
        @test r.indices[1] isa DnIdx
        @test r.indices[1].parent.label == :tea
        @test r.indices[2] isa DnIdx
        @test r.indices[2].parent.label == :teb
    end

    @testset "_parse_to_texpr — rank-0 tensor" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)

        r = _parse_to_texpr("RicciScalarTECD[]")
        @test r isa TTensor
        @test r.head.name == :RicciScalarTECD
        @test isempty(r.indices)
    end

    @testset "_parse_to_texpr — contravariant index" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TEV, ["tea"], :TE4)

        r = _parse_to_texpr("TEV[tea]")
        @test r isa TTensor
        @test r.indices[1] isa Idx
        @test r.indices[1].label == :tea
    end

    @testset "_parse_to_texpr — product with integer coefficient" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)

        # Engine format (space)
        r = _parse_to_texpr("2 TET[-tea,-teb]")
        @test r isa TProd
        @test r.coeff == 2//1
        @test length(r.factors) == 1
        @test r.factors[1] isa TTensor

        r2 = _parse_to_texpr("-TET[-tea,-teb]")
        @test r2 isa TProd
        @test r2.coeff == -1//1
    end

    @testset "_parse_to_texpr — product with rational coefficient" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)

        # Engine formats: "(1/2) Name" and "-(3/2)" pure scalar
        r = _parse_to_texpr("(1/2) TET[-tea,-teb]")
        @test r isa TProd
        @test r.coeff == 1//2

        r2 = _parse_to_texpr("(-3/2) TET[-tea,-teb]")
        @test r2 isa TProd
        @test r2.coeff == -3//2

        # "-(n/d)" format (engine outputs this for negative rational scalars)
        r3 = _parse_to_texpr("-(3/2)")
        @test r3 isa TScalar
        @test r3.value == -3//2
    end

    @testset "_parse_to_texpr — tensor product (no coefficient)" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)
        def_tensor!(:TEV, ["tea"], :TE4)

        # Engine format: space-separated
        r = _parse_to_texpr("TET[-tea,-teb] TEV[tea]")
        @test r isa TProd
        @test r.coeff == 1//1
        @test length(r.factors) == 2
    end

    @testset "_parse_to_texpr — sum" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)
        def_tensor!(:TES, ["-tea", "-teb"], :TE4)

        r = _parse_to_texpr("TET[-tea,-teb] + TES[-tea,-teb]")
        @test r isa TSum
        @test length(r.terms) == 2
        @test r.terms[1] isa TTensor
        @test r.terms[2] isa TTensor
    end

    @testset "_parse_to_texpr — difference" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)
        def_tensor!(:TES, ["-tea", "-teb"], :TE4)

        r = _parse_to_texpr("TET[-tea,-teb] - TES[-tea,-teb]")
        @test r isa TSum
        @test length(r.terms) == 2
        # Second term should be negated
        @test r.terms[2] isa TProd
        @test (r.terms[2]::TProd).coeff == -1//1
    end

    @testset "_parse_to_texpr — multi-term sum with coefficients" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)
        def_tensor!(:TES, ["-tea", "-teb"], :TE4)

        # Engine format: space-separated coefficients
        r = _parse_to_texpr("2 TET[-tea,-teb] + (1/2) TES[-tea,-teb]")
        @test r isa TSum
        @test length(r.terms) == 2
        @test (r.terms[1]::TProd).coeff == 2//1
        @test (r.terms[2]::TProd).coeff == 1//2
    end

    @testset "_parse_to_texpr — CovD expression" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TEphi, String[], :TE4)

        r = _parse_to_texpr("TECD[-tea][TEphi[]]")
        @test r isa TCovD
        @test r.covd == :TECD
        @test r.index isa DnIdx
        @test r.index.parent.label == :tea
        @test r.operand isa TTensor
        @test (r.operand::TTensor).head.name == :TEphi
    end

    @testset "_parse_to_texpr — nested CovD" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TEphi, String[], :TE4)

        r = _parse_to_texpr("TECD[-tea][TECD[-teb][TEphi[]]]")
        @test r isa TCovD
        @test r.operand isa TCovD
        @test (r.operand::TCovD).index.parent.label == :teb
    end

    @testset "_to_string round-trip through _parse_to_texpr" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)
        def_tensor!(:TES, ["-tea", "-teb"], :TE4)
        def_tensor!(:TEV, ["tea"], :TE4)

        # Strings in engine/space format (same format _to_string now produces)
        exprs = [
            "TET[-tea,-teb]",
            "2 TET[-tea,-teb]",
            "(1/2) TES[-tea,-teb]",
            "-TET[-tea,-teb]",
            "TET[-tea,-teb] + TES[-tea,-teb]",
            "TET[-tea,-teb] - TES[-tea,-teb]",
            "TET[-tea,-teb] TEV[tea]",
        ]
        for s in exprs
            @test _to_string(_parse_to_texpr(s)) == s
        end
    end

    @testset "_parse_to_texpr — bare name (TSymbol)" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])

        r = _parse_to_texpr("SomeBareSymbol")
        @test r isa TSymbol
        @test r.name == :SomeBareSymbol
        @test _to_string(r) == "SomeBareSymbol"
        @test r == "SomeBareSymbol"
    end

    @testset "TExpr == String equality" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_tensor!(:TET, ["-tea", "-teb"], :TE4)

        @indices TE4 tea teb
        T = tensor(:TET)

        @test T[-tea, -teb] == "TET[-tea,-teb]"
        @test "TET[-tea,-teb]" == T[-tea, -teb]
        @test TScalar(0//1) == "0"
        @test TScalar(3//2) == "(3/2)"
    end

    @testset "ToCanonical — TExpr input returns TExpr" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")

        @indices TE4 tea teb tec ted
        T = tensor(:TET)

        zero_result = ToCanonical(T[-teb, -tea] - T[-tea, -teb])
        @test zero_result isa TExpr
        @test zero_result == "0"

        # Unchanged tensor — result is still TExpr
        canon = ToCanonical(T[-tea, -teb])
        @test canon isa TExpr
    end

    @testset "Contract — TExpr input returns TExpr" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TEV, ["tea"], :TE4)

        @indices TE4 tea teb
        V = tensor(:TEV)
        g = tensor(:TEg)

        result = Contract(V[tea] * g[-tea, -teb])
        @test result isa TExpr
        # Result should match space-format string equivalent
        @test result == Contract("TEV[tea] TEg[-tea,-teb]")
    end

    @testset "Simplify — TExpr input returns TExpr" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)

        @indices TE4 tea teb
        g = tensor(:TEg)

        result = Simplify(g[-tea, -teb])
        @test result isa TExpr
        @test result == Simplify("TEg[-tea,-teb]")
    end

    @testset "TExpr chaining — result feeds next call" begin
        reset_state!()
        def_manifold!(:TE4, 4, [:tea, :teb, :tec, :ted])
        def_metric!(-1, "TEg[-tea,-teb]", :TECD)
        def_tensor!(:TET, ["-tea", "-teb"], :TE4; symmetry_str="Symmetric[{-tea,-teb}]")

        @indices TE4 tea teb
        T = tensor(:TET)
        g = tensor(:TEg)

        # Chain: Contract result (TExpr) fed into ToCanonical
        contracted = Contract(T[-tea, -teb] * g[-tea, -teb])
        @test contracted isa TExpr
        final = ToCanonical(contracted)
        @test final isa TExpr
    end
end # @testset "TExpr"
