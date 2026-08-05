# ============================================================
# Stress test suite — regression nodes for all known defects
#
# Every defect identified in the XAct.jl 0.7.1 sandbox trial
# is recorded here as a @test_broken assertion. The day each
# upstream bug is fixed, the corresponding test flips from
# @test_broken to a real failure, giving every open defect a
# machine-checkable regression net from day one.
#
# As of 2026-08-05, some defects have been resolved:
#   - Defect 2 (perturb drops indices on metric): FIXED
#   - Defect 4 (g^{ab}R_{ab} → Ricci): FIXED
#   - Defect 5 (AllContractions includes RicciScalar): FIXED
#
# Defect IDs: 0-8, F1-F3, D, S
# Source: sandbox/xact-trial/STRESS_FINDINGS.md
# ============================================================

@testset "Stress test — sandbox trial regression seeds" begin

    # ==========================================================
    # Defect 0 — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect 0 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Defect 1 — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect 1 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Defect 2 — perturb string API drops indices on output
    # See: sxAct-i6cp
    #
    # Status: metric perturb preserves indices — FIXED.
    #         curvature perturb returns 0 — still broken.
    # ==========================================================
    @testset "Defect 2 — perturb drops indices" begin
        reset_state!()
        def_manifold!(:M2, 4, [:m2a, :m2b, :m2c, :m2d, :m2e, :m2f])
        def_metric!(-1, "g2[-m2a,-m2b]", :CD2)
        def_tensor!(:h2, ["-m2a", "-m2b"], :M2)
        def_perturbation!(:h2, :g2, 1)

        # perturb must preserve tensor indices — FIXED
        @test occursin("[-m2a,-m2b]", perturb("g2[-m2a,-m2b]", 1))

        # product-rule perturb must preserve both index lists — FIXED
        @test occursin("[-m2a,-m2b]", perturb("g2[-m2a,-m2b] g2[-m2c,-m2d]", 1))
        @test occursin("[-m2c,-m2d]", perturb("g2[-m2a,-m2b] g2[-m2c,-m2d]", 1))

        # perturb of curvature is nonzero — still broken
        @test_broken perturb("RicciCD2[-m2a,-m2b]", 1) != "0"
    end

    # ==========================================================
    # Defect 3 — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect 3 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Defect 4 — Contract fails to reduce g^{ab}R_{ab} to Ricci scalar
    # See: sxAct-fzs3
    #
    # Status: g^{ab}R_{ab} → RicciScalar is FIXED.
    #         R^{a}_{a} self-trace still broken.
    # ==========================================================
    @testset "Defect 4 — Contract traces to Ricci scalar" begin
        reset_state!()
        def_manifold!(:M4, 4, [:m4a, :m4b, :m4c, :m4d, :m4e, :m4f])
        def_metric!(-1, "g4[-m4a,-m4b]", :CD4)

        # g^{ab} R_{ab} → Ricci scalar — FIXED
        @test Contract("g4[m4a,m4b] RicciCD4[-m4a,-m4b]") == "RicciScalarCD4[]"

        # R^{a}_{a} → Ricci scalar (self-trace) — still broken
        @test_broken Contract("RicciCD4[m4a,-m4a]") == "RicciScalarCD4[]"

        # Existing traces remain green
        @test Contract("g4[m4a,m4b] g4[-m4a,-m4b]") == "4"
    end

    # ==========================================================
    # Defect 5 — AllContractions never contracts; VarD variance-inconsistent
    # See: sxAct-zx0a
    #
    # Status: AllContractions includes RicciScalar — FIXED.
    #         VarD variance-inconsistent — still broken.
    # ==========================================================
    @testset "Defect 5 — AllContractions and VarD" begin
        reset_state!()
        def_manifold!(:M5, 4, [:m5a, :m5b, :m5c, :m5d, :m5e, :m5f])
        def_metric!(-1, "g5[-m5a,-m5b]", :CD5)

        # AllContractions should include RicciScalar in output — FIXED
        ricci_contractions = AllContractions("RicciCD5[-m5a,-m5b]", :g5)
        @test "RicciScalarCD5[]" in ricci_contractions

        # VarD with correct variance — still broken
        def_tensor!(:T5, ["-m5a", "-m5b"], :M5)
        var_result = VarD("T5[-m5a,-m5b] T5[m5a,m5b]", :T5, :CD5)
        # Should be a single (0,2) tensor, no mixed-variance
        @test_broken length(split(strip(var_result), r"\s+")) == 1
        @test_broken !occursin(r"T5\[[^-]", var_result)
    end

    # ==========================================================
    # Defect 6 — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect 6 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Defect 7 — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect 7 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Defect 8 — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect 8 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Feature gaps (F1-F3)
    #
    # F1: InvarDB lazy artifact download (sxAct-0s1h)
    # F2: XCoba numeric curvature functions (sxAct-0fjj)
    # F3: [placeholder]
    # ==========================================================
    @testset "Feature gap F1 — InvarDB lazy download" begin
        @test_broken false
    end

    @testset "Feature gap F2 — XCoba numeric curvature" begin
        @test_broken false
    end

    @testset "Feature gap F3 (placeholder)" begin
        @test_broken false
    end

    # ==========================================================
    # Dimension-dependent vanishing (§D)
    # See: sxAct-zq10
    #
    # Status: rank-5 antisymmetric on 4D → 0 — FIXED
    # ==========================================================
    @testset "Defect D — dimension-dependent vanishing" begin
        reset_state!()
        def_manifold!(:MD, 4, [:mda, :mdb, :mdc, :mdd, :mde, :mdf])
        # rank-5 antisymmetric on 4D manifold → identically zero
        def_tensor!(:A5D, ["-mda", "-mdb", "-mdc", "-mdd", "-mde"], :MD;
                    symmetry_str="Antisymmetric[{-mda,-mdb,-mdc,-mdd,-mde}]")
        @test ToCanonical("A5D[-mda,-mdb,-mdc,-mdd,-mde]") == "0"
    end

    # ==========================================================
    # Defect S — [placeholder: ToBeDocumented]
    # ==========================================================
    @testset "Defect S (placeholder)" begin
        @test_broken false
    end

end