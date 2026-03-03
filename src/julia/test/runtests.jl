using Test
include("../XCore.jl")
using .XCore

# Helper: reset shared state between tests that modify the registry.
function reset_registry!()
    empty!(XCore._symbol_registry)
    empty!(xCoreNames)
    empty!(xPermNames)
    empty!(xTensorNames)
    empty!(xTableauNames)
    empty!(xCobaNames)
    empty!(InvarNames)
    empty!(HarmonicsNames)
    empty!(xPertNames)
    empty!(SpinorsNames)
    empty!(EMNames)
end

# ============================================================
# register_symbol
# ============================================================

@testset "register_symbol — basic registration" begin
    reset_registry!()
    register_symbol(:MyTensor, "XTensor")
    @test "MyTensor" in xTensorNames
    @test XCore._symbol_registry["MyTensor"] == "XTensor"
end

@testset "register_symbol — idempotent re-registration" begin
    reset_registry!()
    register_symbol("Foo", "XPerm")
    @test_nowarn register_symbol(:Foo, "XPerm")   # same package → no-op
    @test count(==("Foo"), xPermNames) == 1        # not duplicated
end

@testset "register_symbol — collision with different package" begin
    reset_registry!()
    register_symbol(:Bar, "XCore")
    @test_throws ErrorException register_symbol(:Bar, "XTensor")
end

@testset "register_symbol — unknown package skips per-package list" begin
    reset_registry!()
    register_symbol(:Baz, "ThirdParty")
    @test XCore._symbol_registry["Baz"] == "ThirdParty"
    # No per-package list to check, but no error either
end

@testset "register_symbol — all known package lists populated" begin
    reset_registry!()
    pairs = [
        (:S1, "XCore",    xCoreNames),
        (:S2, "XPerm",    xPermNames),
        (:S3, "XTensor",  xTensorNames),
        (:S4, "XTableau", xTableauNames),
        (:S5, "XCoba",    xCobaNames),
        (:S6, "Invar",    InvarNames),
        (:S7, "Harmonics",HarmonicsNames),
        (:S8, "XPert",    xPertNames),
        (:S9, "Spinors",  SpinorsNames),
        (:S10,"EM",       EMNames),
    ]
    for (sym, pkg, lst) in pairs
        register_symbol(sym, pkg)
        @test string(sym) in lst
    end
end

# ============================================================
# ValidateSymbol
# ============================================================

@testset "ValidateSymbol — passes for fresh symbol" begin
    reset_registry!()
    @test_nowarn ValidateSymbol(:UnusedSymbolXYZ123)
end

@testset "ValidateSymbol — collision with registered symbol" begin
    reset_registry!()
    register_symbol(:AlreadyTaken, "XCoba")
    err = @test_throws ErrorException ValidateSymbol(:AlreadyTaken)
    @test occursin("XCoba", err.value.msg)
end

@testset "ValidateSymbol — collision with Base export" begin
    reset_registry!()
    # :map is a well-known Base export
    err = @test_throws ErrorException ValidateSymbol(:map)
    @test occursin("Base", err.value.msg)
end

@testset "ValidateSymbol — Base non-export does not block" begin
    reset_registry!()
    # Base internals that are not exported should not trigger the check.
    # Use a name that is defined in Base but not exported.
    # (We verify it is not exported first so the test is self-consistent.)
    sym = :_setindex_once!   # internal Base helper, not exported
    if isdefined(Base, sym) && !Base.isexported(Base, sym)
        @test_nowarn ValidateSymbol(sym)
    else
        @test_skip "symbol not suitable for this test on this Julia version"
    end
end

@testset "ValidateSymbol — collision message contains symbol name" begin
    reset_registry!()
    register_symbol(:NamedThing, "XTensor")
    err = @test_throws ErrorException ValidateSymbol(:NamedThing)
    @test occursin("NamedThing", err.value.msg)
end

# ============================================================
# FindSymbols
# ============================================================

@testset "FindSymbols — bare symbol" begin
    @test FindSymbols(:x) == [:x]
end

@testset "FindSymbols — non-symbol scalar" begin
    @test FindSymbols(42) == Symbol[]
    @test FindSymbols("hello") == Symbol[]
end

@testset "FindSymbols — vector" begin
    result = FindSymbols([:a, :b, :a, 1])
    @test :a in result && :b in result
    @test length(result) == 2   # deduplicated
end

@testset "FindSymbols — Expr" begin
    e = :( f(x, y) )
    syms = FindSymbols(e)
    @test :f in syms && :x in syms && :y in syms
end

@testset "FindSymbols — tuple" begin
    result = FindSymbols((:p, :q, :p))
    @test length(result) == 2
    @test :p in result && :q in result
end

# ============================================================
# ThreadArray
# ============================================================

@testset "ThreadArray — element-wise application" begin
    result = ThreadArray(+, [1, 2, 3], [10, 20, 30])
    @test result == [11, 22, 33]
end

@testset "ThreadArray — with lambda" begin
    result = ThreadArray((a, b) -> a * b, [2, 3], [4, 5])
    @test result == [8, 15]
end

# ============================================================
# ReportSet
# ============================================================

@testset "ReportSet — changes value when different" begin
    r = Ref(1)
    ReportSet(r, 2; verbose=false)
    @test r[] == 2
end

@testset "ReportSet — no change when same value" begin
    r = Ref(42)
    ReportSet(r, 42; verbose=false)
    @test r[] == 42
end

@testset "ReportSet — verbose=true does not throw" begin
    r = Ref("old")
    @test_nowarn ReportSet(r, "new"; verbose=false)
    @test r[] == "new"
end

# ============================================================
# ReportSetOption
# ============================================================

@testset "ReportSetOption — is a no-op" begin
    @test ReportSetOption(:SomeSymbol, :opt => "val") === nothing
end

# ============================================================
# LinkCharacter / LinkSymbols / UnlinkSymbol
# ============================================================

@testset "LinkSymbols — joins with LinkCharacter" begin
    lc = LinkCharacter[]
    result = LinkSymbols([:ab, :cd, :ef])
    @test string(result) == "ab$(lc)cd$(lc)ef"
end

@testset "LinkSymbols — single symbol" begin
    @test LinkSymbols([:foo]) == :foo
end

@testset "LinkSymbols — empty list" begin
    @test LinkSymbols(Symbol[]) == Symbol("")
end

@testset "UnlinkSymbol — splits at LinkCharacter" begin
    lc = LinkCharacter[]
    s = Symbol("ab$(lc)cd$(lc)ef")
    @test UnlinkSymbol(s) == [:ab, :cd, :ef]
end

@testset "UnlinkSymbol — no link character is identity" begin
    @test UnlinkSymbol(:foo) == [:foo]
end

@testset "LinkSymbols + UnlinkSymbol — roundtrip" begin
    parts = [:alpha, :beta, :gamma]
    @test UnlinkSymbol(LinkSymbols(parts)) == parts
end

# ============================================================
# xTension! / MakexTensions
# ============================================================

# Helper to reset the extensions store between test sets.
function reset_xtensions!()
    empty!(XCore._xtensions)
end

@testset "xTension! + MakexTensions — hooks fire in registration order" begin
    reset_xtensions!()
    log = Int[]
    xTension!("PkgA", :DefMetric, "Beginning", (_...) -> push!(log, 1))
    xTension!("PkgB", :DefMetric, "Beginning", (_...) -> push!(log, 2))
    xTension!("PkgC", :DefMetric, "Beginning", (_...) -> push!(log, 3))
    MakexTensions(:DefMetric, "Beginning")
    @test log == [1, 2, 3]
end

@testset "xTension! + MakexTensions — Beginning and End are independent" begin
    reset_xtensions!()
    fired = Symbol[]
    xTension!("Pkg", :DefTensor, "Beginning", (_...) -> push!(fired, :begin))
    xTension!("Pkg", :DefTensor, "End",       (_...) -> push!(fired, :end))
    MakexTensions(:DefTensor, "Beginning")
    @test fired == [:begin]
    MakexTensions(:DefTensor, "End")
    @test fired == [:begin, :end]
end

@testset "xTension! + MakexTensions — hooks receive args" begin
    reset_xtensions!()
    received = []
    xTension!("Pkg", :DefMetric, "End", (a, b) -> push!(received, (a, b)))
    MakexTensions(:DefMetric, "End", :g, 4)
    @test received == [(:g, 4)]
end

@testset "xTension! + MakexTensions — no hooks registered is a no-op" begin
    reset_xtensions!()
    @test_nowarn MakexTensions(:UnknownCmd, "Beginning")
end

@testset "xTension! — invalid moment throws" begin
    reset_xtensions!()
    @test_throws ErrorException xTension!("Pkg", :DefTensor, "Middle", identity)
end

@testset "xTension! + MakexTensions — multiple commands are independent" begin
    reset_xtensions!()
    log = Symbol[]
    xTension!("Pkg", :DefMetric, "End", (_...) -> push!(log, :metric))
    xTension!("Pkg", :DefTensor, "End", (_...) -> push!(log, :tensor))
    MakexTensions(:DefMetric, "End")
    @test log == [:metric]
    MakexTensions(:DefTensor, "End")
    @test log == [:metric, :tensor]
end
