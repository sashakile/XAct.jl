# Tests for XTensor.jl — DefManifold, DefMetric, DefTensor, ToCanonical.
using Test

include(joinpath(@__DIR__, "..", "XTensor.jl"))
using .XTensor

@testset "XTensor" begin

    # Reset state before each top-level testset
    reset_state!()

    @testset "DefManifold" begin
        reset_state!()
        m = def_manifold!(:Tn4, 4, [:tna, :tnb, :tnc, :tnd])
        @test m.name == :Tn4
        @test m.dimension == 4
        @test ManifoldQ(:Tn4)
        @test !ManifoldQ(:NotDefined)
        @test Dimension(:Tn4) == 4
        @test :Tn4 in list_manifolds()

        # VBundle auto-created
        @test VBundleQ(:TangentTn4)
        @test IndicesOfVBundle(:TangentTn4) == [:tna, :tnb, :tnc, :tnd]

        # Duplicate definition throws
        @test_throws Exception def_manifold!(:Tn4, 4, [:tna, :tnb, :tnc, :tnd])
    end

    @testset "DefTensor" begin
        reset_state!()
        def_manifold!(:Tm4, 4, [:tma, :tmb, :tmc, :tmd])

        # Symmetric tensor
        ts = def_tensor!(:TmS, ["-tma", "-tmb"], :Tm4; symmetry_str="Symmetric[{-tma,-tmb}]")
        @test TensorQ(:TmS)
        @test ts.symmetry.type == :Symmetric
        @test ts.symmetry.slots == [1, 2]

        # Antisymmetric tensor
        ta = def_tensor!(:TmA, ["-tma", "-tmb"], :Tm4; symmetry_str="Antisymmetric[{-tma,-tmb}]")
        @test ta.symmetry.type == :Antisymmetric

        # No symmetry
        tv = def_tensor!(:TmV, ["tma"], :Tm4)
        @test tv.symmetry.type == :NoSymmetry

        @test :TmS in list_tensors()
    end

    @testset "DefMetric — auto-curvature tensors" begin
        reset_state!()
        def_manifold!(:Cnm, 4, [:cna, :cnb, :cnc, :cnd])
        def_metric!(-1, "Cng[-cna,-cnb]", :Cnd)

        @test TensorQ(:Cng)
        @test TensorQ(:RiemannCnd)
        @test TensorQ(:RicciCnd)
        @test TensorQ(:RicciScalarCnd)
        @test TensorQ(:EinsteinCnd)
        @test TensorQ(:WeylCnd)

        # Riemann has RiemannSymmetric symmetry
        r = get_tensor(:RiemannCnd)
        @test r.symmetry.type == :RiemannSymmetric
        @test r.symmetry.slots == [1, 2, 3, 4]

        # Ricci is symmetric
        rc = get_tensor(:RicciCnd)
        @test rc.symmetry.type == :Symmetric

        # RicciScalar is scalar (no slots)
        rcs = get_tensor(:RicciScalarCnd)
        @test isempty(rcs.slots)
    end

    @testset "ToCanonical — zero and identity" begin
        reset_state!()
        @test ToCanonical("0") == "0"
        @test ToCanonical("") == "0"
    end

    @testset "ToCanonical — symmetric swap" begin
        reset_state!()
        def_manifold!(:Cnm, 4, [:cna, :cnb, :cnc, :cnd])
        def_tensor!(:Cns, ["-cna", "-cnb"], :Cnm; symmetry_str="Symmetric[{-cna,-cnb}]")

        # Cns[-cna,-cnb] - Cns[-cnb,-cna] == 0
        result = ToCanonical("Cns[-cna,-cnb] - Cns[-cnb,-cna]")
        @test result == "0"

        # Single term is canonical
        result2 = ToCanonical("Cns[-cna,-cnb]")
        @test result2 == "Cns[-cna,-cnb]"
    end

    @testset "ToCanonical — antisymmetric sum" begin
        reset_state!()
        def_manifold!(:Cnm, 4, [:cna, :cnb, :cnc, :cnd])
        def_tensor!(:Cna, ["-cna", "-cnb"], :Cnm; symmetry_str="Antisymmetric[{-cna,-cnb}]")

        # Cna[-cna,-cnb] + Cna[-cnb,-cna] == 0
        result = ToCanonical("Cna[-cna,-cnb] + Cna[-cnb,-cna]")
        @test result == "0"
    end

    @testset "ToCanonical — idempotency" begin
        reset_state!()
        def_manifold!(:Cnm, 4, [:cna, :cnb, :cnc, :cnd])
        def_tensor!(:Cns, ["-cna", "-cnb"], :Cnm; symmetry_str="Symmetric[{-cna,-cnb}]")
        def_tensor!(:Cnv, ["cna"], :Cnm)

        expr = "Cns[-cna,-cnb] + Cnv[cna]"
        once  = ToCanonical(expr)
        twice = ToCanonical(once)
        @test once == twice
    end

    @testset "ToCanonical — Riemann antisymmetry" begin
        reset_state!()
        def_manifold!(:Cnm, 4, [:cna, :cnb, :cnc, :cnd])
        def_metric!(-1, "Cng[-cna,-cnb]", :Cnd)

        # R[-a,-b,-c,-d] + R[-b,-a,-c,-d] == 0
        result = ToCanonical("RiemannCnd[-cna,-cnb,-cnc,-cnd] + RiemannCnd[-cnb,-cna,-cnc,-cnd]")
        @test result == "0"

        # R[-a,-b,-c,-d] + R[-a,-b,-d,-c] == 0
        result2 = ToCanonical("RiemannCnd[-cna,-cnb,-cnc,-cnd] + RiemannCnd[-cna,-cnb,-cnd,-cnc]")
        @test result2 == "0"

        # R[-a,-b,-c,-d] - R[-c,-d,-a,-b] == 0 (pair exchange)
        result3 = ToCanonical("RiemannCnd[-cna,-cnb,-cnc,-cnd] - RiemannCnd[-cnc,-cnd,-cna,-cnb]")
        @test result3 == "0"
    end

    @testset "ToCanonical — Riemann idempotency" begin
        reset_state!()
        def_manifold!(:Cnm, 4, [:cna, :cnb, :cnc, :cnd])
        def_metric!(-1, "Cng[-cna,-cnb]", :Cnd)

        expr  = "RiemannCnd[-cna,-cnb,-cnc,-cnd]"
        once  = ToCanonical(expr)
        twice = ToCanonical(once)
        @test once == twice
    end

    @testset "ToCanonical — product expression" begin
        reset_state!()
        def_manifold!(:CInv4, 4, [:cia, :cib, :cic, :cid, :cie, :cif])
        def_metric!(-1, "CIg[-cia,-cib]", :CID)

        # Kretschner: R[-a,-b,-c,-d] R[a,b,c,d] - R[-c,-d,-a,-b] R[c,d,a,b] = 0
        # (dummy relabeling + pair exchange)
        result = ToCanonical("RiemannCID[-cia,-cib,-cic,-cid] RiemannCID[cia,cib,cic,cid] - RiemannCID[-cic,-cid,-cia,-cib] RiemannCID[cic,cid,cia,cib]")
        @test result == "0"
    end

    @testset "ToCanonical — torsion partial-slot antisymmetry" begin
        reset_state!()
        def_manifold!(:QGM4, 4, [:qga, :qgb, :qgc, :qgd, :qge, :qgf])
        def_tensor!(:QGTorsion, ["qga", "-qgb", "-qgc"], :QGM4;
                    symmetry_str="Antisymmetric[{-qgb,-qgc}]")

        # QGTorsion[a,-b,-c] + QGTorsion[a,-c,-b] == 0
        result = ToCanonical("QGTorsion[qga,-qgb,-qgc] + QGTorsion[qga,-qgc,-qgb]")
        @test result == "0"
    end

    @testset "MemberQ and predicates" begin
        reset_state!()
        def_manifold!(:Pm, 3, [:pa, :pb, :pc])
        def_tensor!(:Pv, ["pa"], :Pm)

        @test MemberQ(:Manifolds, :Pm)
        @test MemberQ(:Tensors, :Pv)
        @test !MemberQ(:Manifolds, :Pv)
    end

    @testset "reset_state!" begin
        reset_state!()
        def_manifold!(:Rm, 2, [:ra, :rb])
        @test ManifoldQ(:Rm)
        reset_state!()
        @test !ManifoldQ(:Rm)
        @test isempty(list_manifolds())
    end

    @testset "Contract" begin
        reset_state!()
        def_manifold!(:Cm, 4, [:ca, :cb, :cc, :cd])
        def_metric!(1, "Cg[-ca,-cb]", :Cd)
        def_tensor!(:Cv, ["-ca"], :Cm)

        # SignDetOfMetric
        @test SignDetOfMetric(:Cg) == 1

        # Raise index: g^{ab} v_b → v^a
        @test Contract("Cg[ca,cb] Cv[-cb]") == "Cv[ca]"

        # Lower index: g_{ab} v^b → v_{-a} (result: Cv[-ca])
        @test Contract("Cg[-ca,-cb] Cv[cb]") == "Cv[-ca]"

        # Weyl tracelessness: g^{ac} W_{abcd} = 0
        reset_state!()
        def_manifold!(:Cm4, 4, [:cxa, :cxb, :cxc, :cxd, :cxe, :cxf])
        def_metric!(-1, "CIg[-cxa,-cxb]", :CxD)
        @test Contract("CIg[cxa,cxc] WeylCxD[-cxa,-cxb,-cxc,-cxd]") == "0"

        # Einstein trace in 4D: g^{ab} G_{ab} = -R
        @test Contract("CIg[cxa,cxb] EinsteinCxD[-cxa,-cxb]") == "-RicciScalarCxD[]"
        @test ToCanonical(
            Contract("CIg[cxa,cxb] EinsteinCxD[-cxa,-cxb]") * " + RicciScalarCxD[]"
        ) == "0"
    end

end
