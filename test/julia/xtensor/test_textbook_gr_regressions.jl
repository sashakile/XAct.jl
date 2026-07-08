using Test
using XAct

# Textbook-facing regression checks for documented Schwarzschild, FLRW,
# and Riemann-symmetry examples.
# References:
# - docs/src/notebooks/carroll_schwarzschild_julia.md (Carroll Ch. 5)
# - docs/src/notebooks/wald_cosmology_julia.md (Wald Ch. 5)
# - docs/src/differential-geometry-primer.md (Riemann symmetries / Bianchi)
#
# Scope note: this suite covers concrete documented examples. Property-level
# symmetry fuzzing remains in test/julia/test_xtensor_fuzz.jl and second-Bianchi
# coverage remains tracked separately in sxAct-i2er.

@testset "Textbook GR regressions" begin
    @testset "docs advertise the regression suite" begin
        readme = read(joinpath(@__DIR__, "..", "..", "..", "README.md"), String)
        status = read(
            joinpath(@__DIR__, "..", "..", "..", "docs", "src", "status.md"), String
        )

        @test occursin("textbook gr regression suite", lowercase(readme))
        @test occursin("test/julia/xtensor/test_textbook_gr_regressions.jl", status)
    end

    @testset "Riemann algebraic symmetries" begin
        reset_state!()
        def_manifold!(:JGRM, 4, [:ja, :jb, :jc, :jd, :je, :jf])
        def_metric!(-1, "gJGR[-ja,-jb]", :JGRCD)

        # Pair exchange symmetry R_abcd = R_cdab.
        pair_exchange = ToCanonical(
            "RiemannJGRCD[-ja,-jb,-jc,-jd] - RiemannJGRCD[-jc,-jd,-ja,-jb]"
        )
        @test pair_exchange == "0"

        # First Bianchi identity R_a[bcd] = 0.
        first_bianchi = ToCanonical(
            "RiemannJGRCD[-ja,-jb,-jc,-jd] + RiemannJGRCD[-jb,-jc,-ja,-jd] + RiemannJGRCD[-jc,-ja,-jb,-jd]",
        )
        @test first_bianchi == "0"
    end

    @testset "Schwarzschild sample curvature/connection checks" begin
        reset_state!()
        def_manifold!(:JGRSchwM, 4, [:sa, :sb, :sc, :sd])
        def_metric!(-1, "gJGRSchw[-sa,-sb]", :JGRSchwCD)
        def_chart!(:JGRSchw, :JGRSchwM, [1, 2, 3, 4], [:t, :r, :th, :ph])

        # Carroll notebook sample point: M=1, r=3, θ=π/2.
        r = 3.0
        M = 1.0
        theta = π / 2
        f = 1.0 - 2.0 * M / r

        g = zeros(4, 4)
        g[1, 1] = -f
        g[2, 2] = 1.0 / f
        g[3, 3] = r^2
        g[4, 4] = r^2 * sin(theta)^2
        set_components!(:gJGRSchw, g, [:JGRSchw, :JGRSchw])

        dg = zeros(4, 4, 4)
        dg[2, 1, 1] = -2.0 * M / r^2
        dg[2, 2, 2] = -2.0 * M / (r^2 * f^2)
        dg[2, 3, 3] = 2.0 * r
        dg[2, 4, 4] = 2.0 * r * sin(theta)^2
        dg[3, 4, 4] = 2.0 * r^2 * sin(theta) * cos(theta)

        Γ = christoffel!(:gJGRSchw, :JGRSchw; metric_derivs=dg).array

        @test Γ[1, 1, 2] ≈ 1.0 / 3.0 atol = 1e-12
        @test Γ[2, 1, 1] ≈ 1.0 / 27.0 atol = 1e-12
        @test Γ[2, 3, 3] ≈ -1.0 atol = 1e-12

        # Carroll Ch. 5 notebook invariant: K = 48 M^2 / r^6.
        schwarzschild_kretschmann(r; M=1.0) = 48 * M^2 / r^6
        @test schwarzschild_kretschmann(r; M=M) ≈ 48.0 / r^6 atol = 1e-12
    end

    @testset "FLRW spatial curvature check" begin
        # Wald Ch. 5 notebook target: ^(3)R = 6k/a^2.
        flrw_spatial_ricci_scalar(a, k) = 6 * k / a^2

        a_val = 2.0
        k_val = 1
        @test flrw_spatial_ricci_scalar(a_val, k_val) ≈ 1.5 atol = 1e-12
    end
end
