# Tests for XPerm.jl — permutation utilities and canonicalization.
using Test

include(joinpath(@__DIR__, "..", "XPerm.jl"))
using .XPerm

@testset "XPerm" begin
    @testset "Permutation utilities" begin
        @test identity_perm(4) == [1, 2, 3, 4]
        @test identity_signed_perm(4) == [1, 2, 3, 4, 5, 6]

        p = [2, 1, 4, 3]
        @test perm_sign(p) == 1   # two 2-cycles = even
        @test perm_sign([2, 1, 3]) == -1  # one transposition = odd

        q = [3, 1, 2]
        @test compose(q, q) == [2, 3, 1]
        @test inverse_perm([2, 3, 1]) == [3, 1, 2]

        @test is_identity([1, 2, 3])
        @test !is_identity([2, 1, 3])

        @test on_point([2, 3, 1], 1) == 2
        @test on_list([2, 3, 1], [1, 2]) == [2, 3]
    end

    @testset "Schreier vector" begin
        # Single transposition on 3 points
        g = [2, 1, 3]  # swaps 1 and 2
        sv = schreier_vector(1, [[2, 1, 3]], 3)
        @test sort(sv.orbit) == [1, 2]

        sv2 = schreier_vector(3, [[2, 1, 3]], 3)
        @test sv2.orbit == [3]  # 3 is fixed
    end

    @testset "canonicalize_slots — Symmetric" begin
        # Symmetric tensor: sort indices lexicographically
        idxs = ["-cnb", "-cna"]  # out of order
        (result, sign) = canonicalize_slots(idxs, :Symmetric, [1, 2])
        @test result == ["-cna", "-cnb"]
        @test sign == 1

        # Already canonical
        idxs2 = ["-cna", "-cnb"]
        (result2, sign2) = canonicalize_slots(idxs2, :Symmetric, [1, 2])
        @test result2 == ["-cna", "-cnb"]
        @test sign2 == 1
    end

    @testset "canonicalize_slots — Antisymmetric" begin
        # Antisymmetric swap: T[-b,-a] = -T[-a,-b]
        idxs = ["-cnb", "-cna"]
        (result, sign) = canonicalize_slots(idxs, :Antisymmetric, [1, 2])
        @test result == ["-cna", "-cnb"]
        @test sign == -1

        # Already canonical
        idxs2 = ["-cna", "-cnb"]
        (result2, sign2) = canonicalize_slots(idxs2, :Antisymmetric, [1, 2])
        @test result2 == ["-cna", "-cnb"]
        @test sign2 == 1

        # Repeated index → zero
        idxs3 = ["-cna", "-cna"]
        (result3, sign3) = canonicalize_slots(idxs3, :Antisymmetric, [1, 2])
        @test sign3 == 0
    end

    @testset "canonicalize_slots — partial slots" begin
        # Antisymmetric on slots [2,3] only (like QGTorsion[a,-b,-c])
        idxs = ["qga", "-qgc", "-qgb"]   # slots 2,3 are out of order
        (result, sign) = canonicalize_slots(idxs, :Antisymmetric, [2, 3])
        @test result == ["qga", "-qgb", "-qgc"]
        @test sign == -1

        # Slot 1 unchanged
        @test result[1] == "qga"
    end

    @testset "canonicalize_slots — Riemann" begin
        # R[-a,-b,-c,-d] + R[-b,-a,-c,-d] = 0 (antisym in first pair)
        idxs = ["-cnb", "-cna", "-cnc", "-cnd"]  # swapped first pair
        (result, sign) = canonicalize_slots(idxs, :RiemannSymmetric, [1, 2, 3, 4])
        # Canonical should have a before b → ["-cna", "-cnb", "-cnc", "-cnd"] with sign=-1
        @test result == ["-cna", "-cnb", "-cnc", "-cnd"]
        @test sign == -1

        # Pair exchange: R[-a,-b,-c,-d] = R[-c,-d,-a,-b]
        # R[-c,-d,-a,-b] should canonicalize to R[-a,-b,-c,-d] with sign +1
        idxs2 = ["-cnc", "-cnd", "-cna", "-cnb"]
        (result2, sign2) = canonicalize_slots(idxs2, :RiemannSymmetric, [1, 2, 3, 4])
        @test result2 == ["-cna", "-cnb", "-cnc", "-cnd"]
        @test sign2 == 1

        # Second pair antisymmetry: R[-a,-b,-d,-c] = -R[-a,-b,-c,-d]
        idxs3 = ["-cna", "-cnb", "-cnd", "-cnc"]
        (result3, sign3) = canonicalize_slots(idxs3, :RiemannSymmetric, [1, 2, 3, 4])
        @test result3 == ["-cna", "-cnb", "-cnc", "-cnd"]
        @test sign3 == -1
    end

    @testset "NoSymmetry passthrough" begin
        idxs = ["-cnb", "-cna"]
        (result, sign) = canonicalize_slots(idxs, :NoSymmetry, Int[])
        @test result == idxs
        @test sign == 1
    end

    @testset "symmetric_sgs" begin
        sgs = symmetric_sgs([1, 2], 3)
        @test sgs.n == 3
        @test !sgs.signed
        @test length(sgs.GS) == 1
        @test sgs.GS[1] == [2, 1, 3]  # transposition of slots 1,2
    end

    @testset "antisymmetric_sgs" begin
        sgs = antisymmetric_sgs([1, 2], 3)
        @test sgs.n == 3
        @test sgs.signed
        g = sgs.GS[1]
        @test length(g) == 5  # n+2 = 5
        @test g[1] == 2 && g[2] == 1  # transposition
        @test g[4] == 5 && g[5] == 4  # sign flip
    end

    @testset "riemann_sgs" begin
        sgs = riemann_sgs((1, 2, 3, 4), 4)
        @test sgs.n == 4
        @test sgs.signed
        @test length(sgs.GS) == 3
    end
end
